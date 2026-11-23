import os
import tempfile
import jwt
from pathlib import Path
from datetime import datetime, timezone, timedelta
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp()) / 'test.db')
from fastapi.testclient import TestClient
from backend.app.main import app, limits, hasher
from backend.app.db import Base, SessionLocal, get_db
from backend.app.models import User
from backend.app.routers import recovery
from backend.app.security import JWT_SECRET, SESSION_AUDIENCE, SESSION_ISSUER

def payload(**changes):
    return {'title': 'Water supply issue', 'text': 'No water near the school for three days', 'area': 'Mirpur 10', 'language': 'English', 'occurred_at': (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(), **changes}

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
        client.post('/api/auth/register', json={'email':'citizen@example.org','password':'test-password-123'})
        assert client.post('/api/auth/login',json={'email':'citizen@example.org','password':'test-password-123'}).status_code == 200
        assert client.get('/api/admin/complaints').status_code == 403
        assert client.get('/api/admin/audit').status_code == 403
        with SessionLocal() as db:
            db.add(User(email='admin@example.org',password_hash=hasher.hash('test-admin-password'),role='admin'))
            db.commit()
        assert client.post('/api/auth/login',json={'email':'admin@example.org','password':'test-admin-password'}).status_code == 200
        item=client.post('/api/complaints',json=payload()).json()
        response=client.patch('/api/admin/complaints/'+item['id'],json={'status':'In progress','priority':'High','note':'Verified the incident location with the service team.'})
        assert response.status_code == 200
        assert response.json()['analysis']['requires_review'] is False
        review_log = client.get('/api/admin/audit').json()
        assert any(entry['complaint_id'] == item['id'] for entry in review_log)

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
        assert client.post('/api/auth/register', json=first).status_code == 200
        assert client.post('/api/auth/login', json=first).status_code == 200
        assert client.get('/api/auth/me').json() == {'role': 'citizen', 'email': first['email']}
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
        assert client.post('/api/auth/register', json=second).status_code == 200
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
        client.post('/api/auth/register',json={'email':'session@example.org','password':'session-pass-123'})
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
        assert client.post('/api/auth/register', json=account).status_code == 200
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
    from sqlalchemy import select
    from backend.app.models import PasswordRecoveryGrant

    limits.clear()
    delivered = []
    monkeypatch.setattr(recovery, 'mail_settings', lambda: ('test-key', 'test@example.org', 'https://example.org'))
    monkeypatch.setattr(recovery, 'send_recovery_email', lambda settings, email, code: delivered.append((email, code)))
    account = {'email': 'mail-recovery@example.org', 'password': 'mail-password-123'}
    with TestClient(app) as client:
        assert client.post('/api/auth/register', json=account).status_code == 200
        result = client.post('/api/auth/recovery/email', json={'email': account['email']})
        other = client.post('/api/auth/recovery/email', json={'email': 'unknown-email@example.org'})
        assert result.status_code == other.status_code == 202 and result.json() == other.json()
        assert len(delivered) == 1 and delivered[0][0] == account['email']
        code = delivered[0][1]
        with SessionLocal() as db:
            grant = db.scalar(select(PasswordRecoveryGrant).where(PasswordRecoveryGrant.digest == recovery.digest(code)))
            assert grant.digest != code and grant.method == 'email'
            grant.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        assert client.post('/api/auth/recovery/reset', json={'code': code, 'password': 'changed-password-456'}).status_code == 400
        assert client.post('/api/auth/recovery/email', json={'email': account['email']}).status_code == 202
        assert len(delivered) == 2
        assert client.post('/api/auth/recovery/reset', json={'code': delivered[1][1], 'password': 'changed-password-456'}).status_code == 200


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
            assert client.post('/api/auth/login', json={**account, 'password': 'wrong-admin-password'}).status_code == 401
            login = client.post('/api/auth/login', json=account)
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
        assert client.post('/api/auth/login',json=args).status_code==200
        assert client.get('/api/admin/complaints').status_code == 200
        assert client.post('/api/auth/logout').status_code==200
        assert client.get('/api/admin/complaints').status_code == 401
