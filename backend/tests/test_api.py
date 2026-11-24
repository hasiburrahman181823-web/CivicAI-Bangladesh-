import io
import json
import os
import tempfile
import uuid
import jwt
import av
from argon2 import PasswordHasher
from PIL import Image
from sqlalchemy import select
from pathlib import Path
from datetime import datetime, timezone, timedelta
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp()) / 'test.db')
from fastapi.testclient import TestClient
from backend.app.main import app, limits, hasher
from backend.app.db import Base, SessionLocal, get_db
from backend.app.models import CitizenContact, Complaint, ComplaintIntake, EmailResetCode, TicketEvent, User
from backend.app.routers import recovery, tickets
from backend.app.security import JWT_SECRET, SESSION_AUDIENCE, SESSION_ISSUER

def payload(**changes):
    return {'title': 'Water supply issue', 'text': 'No water near the school for three days', 'area': 'Mirpur 10', 'language': 'English', 'mobile': '01700001234', 'occurred_at': (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(), **changes}


def register_citizen(client, credentials):
    return client.post("/api/auth/register", json={
        "name": "Test Citizen", "mobile": "০১৭০০০০১২৩৪", **credentials,
    })


def test_guest_uploads_are_committed_with_complaints_and_available_to_reviewers():
    limits.clear()
    staff = {"email": "evidence-review@example.org", "password": "test-evidence-review-password"}
    image = io.BytesIO()
    Image.new("RGB", (16, 16), "green").save(image, "PNG")
    clip = io.BytesIO()
    with av.open(clip, "w", format="mp4") as video:
        stream = video.add_stream("libx264", rate=12)
        stream.width = 48
        stream.height = 32
        stream.pix_fmt = "yuv420p"
        video.metadata["comment"] = "private fixture metadata"
        for _ in range(3):
            for packet in stream.encode(av.VideoFrame.from_image(Image.new("RGB", (48, 32), "green"))):
                video.mux(packet)
        for packet in stream.encode():
            video.mux(packet)

    endpoint = "/api/complaints/with-evidence"
    with TestClient(app) as guest, TestClient(app) as admin:
        before = guest.get("/api/public/summary").json()["total"]
        missing_phone = guest.post(endpoint, data={"complaint": json.dumps(payload(mobile=None))},
                                   files={"file": ("proof.png", image.getvalue(), "image/png")})
        assert missing_phone.status_code == 422
        invalid = guest.post(endpoint, data={"complaint": json.dumps(payload())},
                             files={"file": ("proof.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4")})
        assert invalid.status_code == 422
        assert guest.get("/api/public/summary").json()["total"] == before
        with SessionLocal() as db:
            db.add(User(email=staff["email"], password_hash=hasher.hash(staff["password"]), role="admin"))
            db.commit()
        assert admin.post("/api/auth/admin/login", json=staff).status_code == 200

        for name, supplied, original, stored in (
            ("proof.png", "image/png", image.getvalue(), "image/jpeg"),
            ("proof.mp4", "video/mp4", clip.getvalue(), "video/mp4"),
        ):
            response = guest.post(endpoint, data={"complaint": json.dumps(payload())},
                                  files={"file": (name, original, supplied)})
            assert response.status_code == 200, response.text
            saved = response.json()
            path = "/api/tickets/" + saved["id"]
            proof = saved["evidence"]
            assert proof["content_type"] == stored
            assert guest.get(path + "/evidence/" + proof["id"]).status_code == 401
            tracked = guest.post("/api/track/" + saved["id"], json={"tracking_key": saved["tracking_key"]})
            assert tracked.json()["status"] == "Submitted"
            assert admin.get(path).json()["evidence"][0]["id"] == proof["id"]
            downloaded = admin.get(path + "/evidence/" + proof["id"])
            assert downloaded.headers["content-type"] == stored
            assert downloaded.headers["content-disposition"].startswith("attachment;")
            assert downloaded.headers["cache-control"] == "no-store"
            assert len(downloaded.content) == proof["size"]
            assert b"private fixture metadata" not in downloaded.content
        assert guest.get("/api/public/summary").json()["total"] == before + 2


def test_guest_mobile_encryption_and_audited_contact_access(monkeypatch):
    limits.clear()
    staff = {"email": "contact-reviewer@example.org", "password": "test-contact-review-456"}
    with TestClient(app) as client:
        assert client.post("/api/complaints", json=payload(mobile=None)).status_code == 422
        assert client.post("/api/complaints", json=payload(mobile="01234")).status_code == 422
        created = client.post("/api/complaints", json=payload(mobile="+৮৮০ ১৭০০০০১২৩৪"))
        assert created.status_code == 200
        assert "01700001234" not in created.text and "assessment" not in created.json()["analysis"]
        item = created.json()
        path = "/api/tickets/" + item["id"]
        with SessionLocal() as db:
            sealed = db.get(ComplaintIntake, item["id"])
            assert b"+8801700001234" not in sealed.sealed_data and sealed.mobile_verified_at is None
            db.add(User(email=staff["email"], password_hash=hasher.hash(staff["password"]), role="admin"))
            db.commit()
        assert client.get(path).status_code == 401
        assert client.post("/api/auth/admin/login", json=staff).status_code == 200
        assert client.get(path).json()["intake"] == {"mobile": "•••• 1234", "verified": False}
        assert client.get(path).json()["assessment"]["summary"]
        assert client.post(path + "/contact", json={"reason": "Review the contact details"}).status_code == 403
        monkeypatch.setattr(tickets, "contact_reviewers", {staff["email"]})
        contact = client.post(path + "/contact", json={"reason": "Review the contact details"})
        assert contact.json()["mobile"] == "+8801700001234"
        exported = client.get("/api/admin/complaints/export", params={"search": item["id"]})
        assert exported.status_code == 200 and item["id"] in exported.text and "•••• 1234" in exported.text
        assert "+8801700001234" not in exported.text and "source_ip" not in exported.text
        audit = client.get("/api/admin/audit").text
        assert "contact_access" in audit and "complaint_export" in audit and "+8801700001234" not in audit


def test_ticket_ownership_evidence_updates_and_legacy_password():
    limits.clear()
    owner = {"email": "ticket-owner@example.org", "password": "পুরনো-পাসওয়ার্ড" * 7}
    other = {"email": "ticket-other@example.org", "password": "test-ticket-other-456"}
    staff = {"email": "ticket-admin@example.org", "password": "test-ticket-admin-456"}
    with TestClient(app) as client, TestClient(app) as outsider, TestClient(app) as reviewer:
        with SessionLocal() as db:
            db.add(User(email=owner["email"], password_hash=PasswordHasher().hash(owner["password"])))
            db.add(User(email=staff["email"], password_hash=hasher.hash(staff["password"]), role="admin"))
            db.commit()
        assert client.post("/api/auth/login", json=owner).status_code == 200
        with SessionLocal() as db:
            account = db.scalar(select(User).where(User.email == owner["email"]))
            assert account.password_hash.startswith(hasher.prefix)
        assert client.post("/api/auth/logout").status_code == 200
        assert client.post("/api/auth/login", json=owner).status_code == 200
        created = client.post("/api/complaints", json=payload(title="Ticket with evidence", mobile=None))
        path = "/api/tickets/" + created.json()["id"]
        assert client.get(path).status_code == 200 and client.get(path).json()["estimate"] is None
        assert client.post(path + "/evidence", files={"file": ("unsafe.svg", b"<svg/>")}).status_code == 422
        assert client.post(path + "/evidence", files={"file": ("large.png", b"x" * 2100000)}).status_code == 413
        raw = io.BytesIO()
        Image.new("RGB", (10, 10), "green").save(raw, format="PNG")
        uploaded = client.post(path + "/evidence", files={"file": ("evidence.png", raw.getvalue())})
        assert uploaded.status_code == 201
        evidence_url = path + "/evidence/" + uploaded.json()["id"]
        assert "attachment" in client.get(evidence_url).headers["Content-Disposition"]
        assert register_citizen(outsider, other).status_code == 200
        assert outsider.post("/api/auth/login", json=other).status_code == 200
        assert outsider.get(path).status_code == 404 and outsider.get(evidence_url).status_code == 404
        assert outsider.post(path + "/messages", json={"body": "Unauthorized reply"}).status_code == 404
        assert client.post(path + "/messages", json={"body": "The leak spread. Contact me@example.org."}).status_code == 201
        assert reviewer.post("/api/auth/admin/login", json=staff).status_code == 200
        assert reviewer.post(path + "/messages", json={"body": "An inspection is being arranged."}).status_code == 201
        assert reviewer.patch("/api/admin/complaints/" + created.json()["id"], json={
            "status": "In progress", "priority": "High", "note": "Inspection has been arranged.",
        }).status_code == 200
        ticket = client.get(path).json()
        assert [event["status"] for event in ticket["history"]] == ["Submitted", "In progress"]
        assert "me@example.org" not in str(ticket["messages"]) and "intake" not in ticket
        assert {item["kind"] for item in client.get("/api/auth/me/updates").json()} == {"reply", "In progress"}
        assert outsider.get("/api/auth/me/updates").json() == []


def test_local_resolution_estimate_uses_completed_tickets():
    with TestClient(app), SessionLocal() as db:
        start = datetime.now(timezone.utc) - timedelta(days=30)
        for index in range(20):
            item = Complaint(
                id=str(uuid.uuid4()), tracking_hash="0" * 64, title="Resolution example",
                text="Resolution example description", area="Dhaka", language="English",
                occurred_at=start, created_at=start, category="ETA-test", priority="Medium", score=35,
                status="Resolved", analysis={},
            )
            db.add(item)
            db.flush()
            db.add(TicketEvent(complaint_id=item.id, status="Resolved", created_at=start + timedelta(hours=index + 5)))
        db.commit()
        estimate = tickets.estimate_resolution(db, Complaint(category="ETA-test", created_at=start))
        assert estimate["sample_size"] == 20
        assert estimate["typical_min_hours"] <= estimate["median_hours"] <= estimate["typical_max_hours"]

def test_submission_and_private_tracking():
    limits.clear()
    with TestClient(app) as client:
        result = client.post('/api/complaints', json=payload())
        assert result.status_code == 200
        item = result.json()
        assert item['analysis']['confidence'] is None
        assert item['analysis']['requires_review'] is True
        assert client.post('/api/track/'+item['id'], json={'tracking_key': 'wrong'}).status_code == 404
        tracked = client.post('/api/track/'+item['id'], json={'tracking_key': item['tracking_key']})
        assert tracked.status_code == 200
        assert 'tracking_hash' not in tracked.json()

def test_admin_authorization_and_audit():
    limits.clear()
    with TestClient(app) as client:
        assert client.get('/api/admin/complaints').status_code == 401
        register_citizen(client, {'email':'citizen@example.org','password':'test-password-123'})
        assert client.post('/api/auth/login',json={'email':'citizen@example.org','password':'test-password-123'}).status_code == 200
        assert client.get('/api/admin/complaints').status_code == 403
        assert client.get('/api/admin/audit').status_code == 403
        with SessionLocal() as db:
            db.add(User(email='admin@example.org',password_hash=hasher.hash('test-admin-password'),role='admin'))
            db.commit()
        assert client.post('/api/auth/admin/login',json={'email':'admin@example.org','password':'test-admin-password'}).status_code == 200
        item=client.post('/api/complaints',json=payload()).json()
        response=client.patch('/api/admin/complaints/'+item['id'],json={'status':'In progress','priority':'High','note':'Verified the incident location with the service team.'})
        assert response.status_code == 200
        assert response.json()['analysis']['requires_review'] is False
        review_log = client.get('/api/admin/audit').json()
        assert any(entry['complaint_id'] == item['id'] for entry in review_log)

def test_public_summary_publishes_totals_and_hides_small_categories():
    limits.clear()
    with TestClient(app) as client:
        original = client.get('/api/public/summary').json()
        hidden = 'Dashboard-only test category'
        shown = 'Published test category'
        statuses = ['Submitted', 'Under review', 'In progress', 'Resolved', 'Resolved']
        with SessionLocal() as db:
            for category, status in [(hidden, 'Submitted'), *[(shown, status) for status in statuses]]:
                db.add(Complaint(
                    id=str(uuid.uuid4()), tracking_hash='0' * 64, title='Private complaint title',
                    text='Private complaint description', area='Private location', language='Bangla',
                    latitude=23.8, longitude=90.4, occurred_at=datetime.now(timezone.utc),
                    category=category, priority='Low', score=10, status=status, analysis={},
                ))
            db.commit()
        response = client.get('/api/public/summary')
        assert response.status_code == 200
        summary = response.json()
        assert set(summary) == {'total', 'resolved', 'in_progress', 'awaiting_action', 'categories'}
        assert summary['total'] == original['total'] + 6
        assert summary['resolved'] == original['resolved'] + 2
        assert summary['in_progress'] == original['in_progress'] + 1
        assert summary['awaiting_action'] == original['awaiting_action'] + 3
        categories = {item['name']: item['count'] for item in summary['categories']}
        assert categories[shown] == 5 and hidden not in categories
        assert 'Private complaint title' not in response.text and 'Private location' not in response.text
        assert client.get('/api/admin/complaints').status_code == 401

def test_validation_and_throttle():
    limits.clear()
    with TestClient(app) as client:
        assert client.post('/api/complaints',json=payload(text=' '*20)).status_code == 422
        assert client.post('/api/complaints',json=payload(text='x'*1001)).status_code == 422
        assert client.post('/api/complaints',json=payload(latitude=23.8)).status_code == 422
        assert client.post('/api/complaints',json=payload(occurred_at=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat())).status_code == 422
        for _ in range(5):
            assert client.post('/api/auth/login',json={'email':'bad@example.org','password':'incorrect-password'}).status_code == 401
        assert client.post('/api/auth/login',json={'email':'bad@example.org','password':'incorrect-password'}).status_code == 429

def test_profile_lists_only_signed_in_citizens_complaints():
    limits.clear()
    first = {'email': 'profile-one@example.org', 'password': 'profile-one-password'}
    second = {'email': 'profile-two@example.org', 'password': 'profile-two-password'}
    with TestClient(app) as client:
        assert client.get('/api/auth/me/complaints').status_code == 401
        assert client.post('/api/complaints', json=payload(title='Guest report')).status_code == 200
        assert register_citizen(client, first).status_code == 200
        assert client.post('/api/auth/login', json=first).status_code == 200
        assert client.get('/api/auth/me').json()['email'] == first['email']
        assert client.get('/api/auth/me/complaints').json() == []
        response = client.post('/api/complaints', json=payload(title='Owned report'))
        assert response.status_code == 200
        submitted = response.json()
        profile = client.get('/api/auth/me/complaints')
        assert profile.status_code == 200
        assert profile.headers['Cache-Control'] == 'no-store'
        assert profile.json() == [{
            'id': submitted['id'], 'title': submitted['title'], 'area': submitted['area'],
            'status': submitted['status'], 'created_at': datetime.fromisoformat(submitted['created_at']).isoformat(),
        }]
        assert client.post('/api/auth/logout').status_code == 200
        assert client.get('/api/auth/me/complaints').status_code == 401
        assert register_citizen(client, second).status_code == 200
        assert client.post('/api/auth/login', json=second).status_code == 200
        assert client.get('/api/auth/me/complaints').json() == []
        assert client.get('/api/admin/complaints').status_code == 403

def test_security_boundaries(tmp_path):
    limits.clear()
    with TestClient(app) as client:
        response=client.post('/api/complaints',json=payload(text='Water pipe broken. Contact owner@example.com.'))
        assert response.status_code==200
        assert 'owner@example.com' not in response.text
        item=response.json()
        track=client.post('/api/track/'+item['id'],json={'tracking_key':item['tracking_key']})
        assert set(track.json()) == {'id','title','category','priority','status','created_at'}
        assert track.headers['Cache-Control']=='no-store'
        assert client.post('/api/analyze',json=payload()).json().keys().isdisjoint({'duplicate_candidate_count','duplicates'})
        denied=client.post('/api/complaints',json=payload(),headers={'Origin':'https://elsewhere.invalid'})
        assert denied.status_code==403 and denied.headers['X-Frame-Options']=='DENY'
        assert client.post('/api/analyze',content=b' '*25000).status_code==413
        assert client.get('/api/health',headers={'Host':'elsewhere.invalid'}).status_code==400
        assert client.post('/api/auth/login',json={'email':'incorrect','password':'example-validation-marker'}).status_code==422
        response=client.post('/api/auth/login',json={'email':'bad','password':'example-validation-marker'})
        assert 'example-validation-marker' not in response.text
        register_citizen(client, {'email':'session@example.org','password':'session-pass-123'})
        logged=client.post('/api/auth/login',json={'email':'session@example.org','password':'session-pass-123'})
        assert logged.status_code==200 and 'token' not in logged.json()
        assert 'httponly' in logged.headers['Set-Cookie'].lower() and 'samesite=strict' in logged.headers['Set-Cookie'].lower()
        old=client.cookies.get('civicai_session')
        claims = jwt.decode(old, JWT_SECRET, algorithms=['HS256'], issuer=SESSION_ISSUER, audience=SESSION_AUDIENCE)
        assert claims['exp'] - claims['iat'] == 3600
        assert 'email' not in claims and 'role' not in claims
        assert client.get('/api/auth/me').status_code==200
        assert client.post('/api/auth/logout').status_code==200
        assert client.get('/api/auth/me',headers={'Cookie':'civicai_session='+old}).status_code==401

def test_multilingual_triage_preview_returns_explanation():
    limits.clear()
    reports = [
        ('Bangla', 'স্কুলের কাছে পাইপ ভেঙে পানি নেই'),
        ('English', 'No water near the school because the pipe broke'),
        ('Banglish', 'school er kache pani nai, pipe bhanga'),
    ]
    with TestClient(app) as client:
        for language, text in reports:
            response = client.post('/api/analyze', json=payload(language=language, text=text))
            assert response.status_code == 200
            result = response.json()
            assert set(result).issuperset({'category', 'priority', 'score', 'breakdown'})
            assert result['score'] == min(100, sum(step['points'] for step in result['breakdown']))
            assert result['requires_review'] is True
            assert 'tracking_key' not in result


def test_saved_recovery_code_is_single_use_and_revokes_sessions():
    limits.clear()
    account = {'email': 'backup-recovery@example.org', 'password': 'original-password-123'}
    new_password = 'replacement-password-456'
    with TestClient(app) as client:
        assert client.post('/api/auth/recovery/code', json={'password': account['password']}).status_code == 401
        assert register_citizen(client, account).status_code == 200
        assert client.post('/api/auth/login', json=account).status_code == 200
        old_session = client.cookies.get('civicai_session')
        assert client.post('/api/auth/recovery/code', json={'password': 'wrong-password-456'}).status_code == 401
        first = client.post('/api/auth/recovery/code', json={'password': account['password']}).json()['code']
        second = client.post('/api/auth/recovery/code', json={'password': account['password']}).json()['code']
        assert client.post('/api/auth/recovery/reset', json={'code': first, 'password': new_password}).status_code == 400
        assert client.post('/api/auth/recovery/reset', json={'code': second, 'password': new_password}).status_code == 200
        assert client.post('/api/auth/recovery/reset', json={'code': second, 'password': 'another-password-789'}).status_code == 400
        assert client.get('/api/auth/me', headers={'Cookie': 'civicai_session=' + old_session}).status_code == 401
        assert client.post('/api/auth/login', json=account).status_code == 401
        assert client.post('/api/auth/login', json={**account, 'password': new_password}).status_code == 200


def test_email_recovery_has_generic_response_and_expires(monkeypatch):
    limits.clear()
    delivered = []
    monkeypatch.setattr(recovery, 'mail_settings', lambda: ('test-key', 'test@example.org'))
    monkeypatch.setattr(recovery, 'send_recovery_email', lambda settings, email, code: delivered.append((email, code)))
    account = {'email': 'mail-recovery@example.org', 'password': 'mail-password-123'}
    with TestClient(app) as client:
        assert register_citizen(client, account).status_code == 200
        result = client.post('/api/auth/recovery/email', json={'email': account['email']})
        other = client.post('/api/auth/recovery/email', json={'email': 'unknown-email@example.org'})
        assert result.status_code == other.status_code == 202 and result.json() == other.json()
        assert len(delivered) == 1 and delivered[0][0] == account['email']
        code = delivered[0][1]
        assert len(code) == 6 and code.isdigit() and code not in result.text
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == account['email']))
            grant = db.get(EmailResetCode, user.id)
            assert grant.digest == recovery.email_code_digest(user.id, code) and grant.digest != code
            grant.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            grant.issued_at = datetime.now(timezone.utc) - timedelta(minutes=11)
            db.commit()
        confirm = '/api/auth/recovery/email/confirm'
        data = {'email': account['email'], 'code': code, 'password': 'changed-password-456'}
        assert client.post(confirm, json=data).status_code == 400
        assert client.post('/api/auth/recovery/email', json={'email': account['email']}).status_code == 202
        assert len(delivered) == 2
        data['code'] = delivered[1][1]
        assert client.post(confirm, json={**data, 'email': 'unknown-email@example.org'}).status_code == 400
        invalid_code = '000000' if data['code'] != '000000' else '999999'
        assert client.post(confirm, json={**data, 'code': invalid_code}).status_code == 400
        assert client.post(confirm, json=data).status_code == 200
        assert client.post(confirm, json=data).status_code == 400
        assert client.post('/api/auth/login', json={'email': data['email'], 'password': data['password']}).status_code == 200


def test_registration_stores_contact_and_suggestions_need_only_description():
    limits.clear()
    account = {'email': 'registered-details@example.org', 'password': 'valid-test-password'}
    with TestClient(app) as client:
        assert client.post('/api/auth/register', json=account).status_code == 422
        assert register_citizen(client, {**account, 'mobile': 'not-a-number'}).status_code == 422
        assert register_citizen(client, account).status_code == 200
        assert client.post('/api/auth/admin/login', json=account).status_code == 401
        assert client.post('/api/auth/login', json=account).status_code == 200
        assert client.get('/api/auth/me').json() == {
            'name': 'Test Citizen', 'mobile': '•••• 1234', 'email': account['email'], 'role': 'citizen',
        }
        with SessionLocal() as db:
            user_id = db.scalar(select(User.id).where(User.email == account['email']))
            contact = db.get(CitizenContact, user_id)
            assert b'+8801700001234' not in contact.sealed_mobile
        result = client.post('/api/analyze', json={'text': 'pani nai', 'language': 'Banglish'})
        assert result.status_code == 200 and result.json()['category'] == 'Water'


def test_first_admin_setup_requires_operator_code_and_allows_password_sign_in(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    limits.clear()
    owner = 'setup-owner@example.org'
    setup_code = 'a' * 43
    monkeypatch.setenv('CIVICAI_ADMIN_EMAIL', owner)
    monkeypatch.setenv('CIVICAI_ADMIN_SETUP_CODE', setup_code)
    monkeypatch.setenv('CIVICAI_ADMIN_SETUP_EXPIRES', (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
    engine = create_engine('sqlite:///' + str(tmp_path / 'admin-setup.db'))
    Base.metadata.create_all(engine)

    def isolated_db():
        with Session(engine) as db:
            yield db

    monkeypatch.setitem(app.dependency_overrides, get_db, isolated_db)
    try:
        with TestClient(app) as client:
            assert client.post('/api/auth/admin-setup/challenge', json={'code': 'b' * 43}).status_code == 400
            challenge = client.post('/api/auth/admin-setup/challenge', json={'code': setup_code})
            assert challenge.status_code == 200 and challenge.json() == {'email': owner}
            credentials = {'code': setup_code, 'password': 'unique-admin-password-123'}
            assert client.post('/api/auth/admin-setup/complete', json={**credentials, 'code': 'b' * 43}).status_code == 400
            assert client.post('/api/auth/admin-setup/complete', json={**credentials, 'password': 'too-short-123'}).status_code == 422
            assert client.post('/api/auth/admin-setup/complete', json=credentials).status_code == 200
            assert client.post('/api/auth/admin-setup/challenge', json={'code': setup_code}).status_code == 409
            assert client.post('/api/auth/admin-setup/complete', json=credentials).status_code == 409
            account = {'email': owner, 'password': credentials['password']}
            assert client.post('/api/auth/admin/login', json={**account, 'password': 'wrong-admin-password'}).status_code == 401
            assert client.post('/api/auth/login', json=account).status_code == 401
            login = client.post('/api/auth/admin/login', json=account)
            assert login.status_code == 200 and login.json()['role'] == 'admin'
            assert 'Max-Age=900' in login.headers['set-cookie']
            assert client.get('/api/admin/complaints').status_code == 200
            assert client.post('/api/auth/recovery/code', json={'password': account['password']}).status_code == 403
    finally:
        engine.dispose()

def test_previously_enrolled_admin_can_sign_in_with_existing_password():
    from backend.app.models import AdminMFA
    limits.clear()
    with TestClient(app) as client:
        with SessionLocal() as db:
            user=User(email='mfa@example.org',password_hash=hasher.hash('mfa-admin-pass'),role='admin')
            db.add(user)
            db.flush()
            db.add(AdminMFA(user_id=user.id,secret_encrypted='legacy enrollment record'))
            db.commit()
        args={'email':'mfa@example.org','password':'mfa-admin-pass'}
        assert client.post('/api/auth/admin/login',json=args).status_code==200
        assert client.get('/api/admin/complaints').status_code == 200
        assert client.post('/api/auth/logout').status_code==200
        assert client.get('/api/admin/complaints').status_code == 401
