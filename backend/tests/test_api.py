import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
os.environ['DATABASE_URL'] = 'sqlite:///' + str(Path(tempfile.mkdtemp()) / 'test.db')
from fastapi.testclient import TestClient
from backend.app.main import app, limits, hasher
from backend.app.db import SessionLocal
from backend.app.models import User

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
        with SessionLocal() as db:
            db.add(User(email='admin@example.org',password_hash=hasher.hash('test-admin-password'),role='admin'))
            db.commit()
        assert client.post('/api/auth/login',json={'email':'admin@example.org','password':'test-admin-password'}).status_code == 200
        item=client.post('/api/complaints',json=payload()).json()
        response=client.patch('/api/admin/complaints/'+item['id'],json={'status':'In progress','priority':'High','note':'Verified the incident location with the service team.'})
        assert response.status_code == 200
        assert response.json()['analysis']['requires_review'] is False
        assert len(client.get('/api/admin/audit').json()) >= 1

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
        assert client.get('/api/auth/me').status_code==200
        assert client.post('/api/auth/logout').status_code==200
        assert client.get('/api/auth/me',headers={'Cookie':'civicai_session='+old}).status_code==401

def test_authenticator_replay_for_enrolled_admin(monkeypatch):
    import base64
    from cryptography.fernet import Fernet
    from backend.app import mfa
    from backend.app.models import AdminMFA
    limits.clear()
    monkeypatch.setattr(mfa,'ADMIN_MFA_KEY',Fernet.generate_key().decode())
    monkeypatch.setattr(mfa.time,'time',lambda: 59)
    secret=base64.b32encode(b'12345678901234567890').decode()
    with TestClient(app) as client:
        with SessionLocal() as db:
            user=User(email='mfa@example.org',password_hash=hasher.hash('mfa-admin-pass'),role='admin')
            db.add(user)
            db.flush()
            db.add(AdminMFA(user_id=user.id,secret_encrypted=mfa.encrypt_secret(secret)))
            db.commit()
        args={'email':'mfa@example.org','password':'mfa-admin-pass'}
        assert client.post('/api/auth/login',json=args).status_code==401
        assert client.post('/api/auth/login',json={**args,'otp':'287082'}).status_code==200
        assert client.post('/api/auth/logout').status_code==200
        assert client.post('/api/auth/login',json={**args,'otp':'287082'}).status_code==401
