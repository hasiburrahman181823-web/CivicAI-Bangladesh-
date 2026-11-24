"""Single-use citizen recovery and operator-authorized administrator setup."""
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from argon2.exceptions import VerificationError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from ..config import JWT_SECRET, PRODUCTION
from ..db import SessionLocal, get_db
from ..models import EmailResetCode, LoginSession, PasswordRecoveryGrant, User
from ..schemas import AccountEmail, AdminSetup, AdminSetupProof, EmailCodePasswordReset, PasswordReset, RecoveryCodeRequest
from ..security import COOKIE, get_session, guarded_password_operation, hasher, throttle

router = APIRouter(prefix="/api/auth", tags=["account recovery"])
logger = logging.getLogger(__name__)
EMAIL_LIFETIME = timedelta(minutes=10)
EMAIL_RESEND_DELAY = timedelta(seconds=60)
EMAIL_ATTEMPTS = 5
GENERIC_RECOVERY = {"message": "If this account can be recovered by email, a code will be sent."}
INVALID_GRANT = "The recovery code is invalid or has expired"


def digest(code):
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def utc(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def mail_settings():
    key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RECOVERY_FROM_EMAIL", "").strip()
    return (key, sender) if key and sender else None


def admin_setup_settings():
    owner = os.getenv("CIVICAI_ADMIN_EMAIL", "").strip().lower()
    code = os.getenv("CIVICAI_ADMIN_SETUP_CODE", "").strip()
    try:
        expires = datetime.fromisoformat(os.getenv("CIVICAI_ADMIN_SETUP_EXPIRES", ""))
    except ValueError:
        return None
    if owner and len(code) == 43 and code.isascii() and expires.tzinfo:
        if expires > datetime.now(timezone.utc):
            return owner, code
    return None


@router.get("/recovery/options")
def recovery_options(db=Depends(get_db)):
    admin_setup_available = (
        admin_setup_settings() is not None
        and db.scalar(select(User.id).where(User.role == "admin").limit(1)) is None
    )
    return {"email_recovery": mail_settings() is not None, "admin_setup": admin_setup_available}


def replace_grant(db, user_id, method, code_hash, expires_at=None):
    db.execute(delete(PasswordRecoveryGrant).where(
        PasswordRecoveryGrant.user_id == user_id, PasswordRecoveryGrant.method == method,
    ))
    db.add(PasswordRecoveryGrant(user_id=user_id, method=method, digest=code_hash, expires_at=expires_at))


def send_recovery_email(settings, email, code):
    key, sender = settings
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "from": sender, "to": [email], "subject": "CivicAI Bangladesh password reset",
            "text": (
                f"CivicAI Bangladesh-এর পাসওয়ার্ড বদলানোর কোড: {code}\n"
                "কোডটি ১০ মিনিট কার্যকর। এটি কারও সঙ্গে শেয়ার করবেন না।\n\n"
                f"Your CivicAI Bangladesh password reset code is {code}. It expires in 10 minutes. "
                "If you did not request a reset, ignore this email.\n"
            ),
        },
        timeout=8.0,
    )
    response.raise_for_status()


def email_code_digest(user_id, code):
    return hmac.new(JWT_SECRET.encode(), f"civicai:email-reset:{user_id}:{code}".encode(), hashlib.sha256).hexdigest()


def deliver_email_reset(email, settings):
    code = f"{secrets.randbelow(1_000_000):06d}"
    now = datetime.now(timezone.utc)
    try:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email, User.role == "citizen").with_for_update())
            if user is None:
                return
            user_id = user.id
            existing = db.get(EmailResetCode, user_id)
            if existing and utc(existing.issued_at) + EMAIL_RESEND_DELAY > now:
                return
            code_hash = email_code_digest(user_id, code)
            grant = existing or EmailResetCode(user_id=user_id)
            grant.digest, grant.issued_at, grant.expires_at, grant.attempts = code_hash, now, now + EMAIL_LIFETIME, 0
            db.add(grant)
            db.commit()
        try:
            send_recovery_email(settings, email, code)
        except httpx.HTTPError as error:
            logger.warning("Recovery email delivery failed (%s)", type(error).__name__)
            with SessionLocal() as db:
                db.execute(delete(EmailResetCode).where(
                    EmailResetCode.user_id == user_id, EmailResetCode.digest == code_hash, EmailResetCode.issued_at == now,
                ))
                db.commit()
    except Exception as error:
        logger.error("Recovery email request could not be processed (%s)", type(error).__name__)


@router.post("/recovery/email", status_code=202)
def request_email_reset(data: AccountEmail, request: Request, background: BackgroundTasks):
    settings = mail_settings()
    if settings is None:
        raise HTTPException(503, "Email recovery has not been configured")
    throttle(request, "recovery-email", 5)
    throttle(request, "recovery-email-account", 2, identity=data.email)
    background.add_task(deliver_email_reset, data.email, settings)
    return GENERIC_RECOVERY


@router.post("/recovery/code")
def generate_recovery_code(data: RecoveryCodeRequest, request: Request, db=Depends(get_db)):
    user, session = get_session(request, db)
    throttle(request, "recovery-code", 3, identity=str(user.id))
    if user.role != "citizen":
        raise HTTPException(403, "Recovery codes are for citizen accounts")
    user = db.get(User, user.id, with_for_update=True, populate_existing=True)
    if not user or user.role != "citizen" or db.get(LoginSession, session.digest, populate_existing=True) is None:
        raise HTTPException(401, "Please sign in again")
    try:
        guarded_password_operation(hasher.verify, user.password_hash, data.password)
    except VerificationError:
        raise HTTPException(401, "Incorrect current password")
    code = secrets.token_urlsafe(32)
    replace_grant(db, user.id, "backup", digest(code))
    db.commit()
    return {"code": code}


def revoke_account_secrets(db, user_id):
    db.execute(delete(EmailResetCode).where(EmailResetCode.user_id == user_id))
    db.execute(delete(PasswordRecoveryGrant).where(PasswordRecoveryGrant.user_id == user_id))
    db.execute(delete(LoginSession).where(LoginSession.user_id == user_id))


@router.post("/recovery/email/confirm")
def reset_with_email_code(data: EmailCodePasswordReset, request: Request, response: Response, db=Depends(get_db)):
    throttle(request, "recovery-reset", 8)
    throttle(request, "recovery-email-confirm", 8, identity=data.email)
    user = db.scalar(select(User).where(User.email == data.email, User.role == "citizen").with_for_update())
    grant = db.get(EmailResetCode, user.id) if user is not None else None
    if grant is None or grant.attempts >= EMAIL_ATTEMPTS or utc(grant.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(400, INVALID_GRANT)
    if not hmac.compare_digest(grant.digest, email_code_digest(user.id, data.code)):
        grant.attempts += 1
        db.commit()
        raise HTTPException(400, INVALID_GRANT)
    return finish_password_reset(db, user, data.password, response)


@router.post("/recovery/reset")
def reset_password(data: PasswordReset, request: Request, response: Response, db=Depends(get_db)):
    throttle(request, "recovery-reset", 8)
    code_hash = digest(data.code)
    user = db.scalar(
        select(User).join(PasswordRecoveryGrant).where(
            PasswordRecoveryGrant.digest == code_hash, User.role == "citizen",
        ).with_for_update(of=User)
    )
    if user is None:
        raise HTTPException(400, INVALID_GRANT)
    grant = db.scalar(select(PasswordRecoveryGrant).where(PasswordRecoveryGrant.digest == code_hash))
    if grant is None or (grant.expires_at and utc(grant.expires_at) <= datetime.now(timezone.utc)):
        raise HTTPException(400, INVALID_GRANT)
    return finish_password_reset(db, user, data.password, response)


def finish_password_reset(db, user, password, response):
    user.password_hash = guarded_password_operation(hasher.hash, password)
    revoke_account_secrets(db, user.id)
    db.commit()
    response.delete_cookie(COOKIE, path="/", secure=PRODUCTION, httponly=True, samesite="strict")
    return {"message": "Password updated"}


def setup_email(code):
    settings = admin_setup_settings()
    if not settings or not hmac.compare_digest(code, settings[1]):
        raise HTTPException(400, "Administrator setup code is invalid or has expired")
    return settings[0]


def require_first_administrator(db):
    if db.scalar(select(User.id).where(User.role == "admin").limit(1)) is not None:
        raise HTTPException(409, "An administrator is already set up")


@router.post("/admin-setup/challenge")
def admin_setup_challenge(data: AdminSetupProof, request: Request, db=Depends(get_db)):
    throttle(request, "admin-setup-challenge", 5)
    email = setup_email(data.code)
    require_first_administrator(db)
    return {"email": email}


@router.post("/admin-setup/complete")
def complete_admin_setup(data: AdminSetup, request: Request, response: Response, db=Depends(get_db)):
    throttle(request, "admin-setup-complete", 5)
    email = setup_email(data.code)
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    require_first_administrator(db)
    password_hash = guarded_password_operation(hasher.hash, data.password)
    if user is None:
        user = User(email=email, password_hash=password_hash, role="admin")
        db.add(user)
    else:
        user.role = "admin"
        user.password_hash = password_hash
        revoke_account_secrets(db, user.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "The account changed during setup. Please try again.")
    response.delete_cookie(COOKIE, path="/", secure=PRODUCTION, httponly=True, samesite="strict")
    return {"email": email, "message": "Administrator setup completed"}
