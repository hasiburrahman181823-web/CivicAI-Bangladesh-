"""Single-use citizen recovery and operator-authorized administrator setup."""
import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

import httpx
from argon2.exceptions import VerificationError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from ..config import PRODUCTION
from ..db import SessionLocal, get_db
from ..models import LoginSession, PasswordRecoveryGrant, User
from ..schemas import AccountEmail, AdminSetup, AdminSetupProof, PasswordReset, RecoveryCodeRequest
from ..security import COOKIE, get_session, guarded_password_operation, hasher, throttle

router = APIRouter(prefix="/api/auth", tags=["account recovery"])
logger = logging.getLogger(__name__)
EMAIL_LIFETIME = timedelta(minutes=20)
GENERIC_RECOVERY = {"message": "If this account can be recovered by email, a reset link will be sent."}
INVALID_GRANT = "The recovery code is invalid or has expired"


def digest(code):
    return hashlib.sha256(code.encode("ascii")).hexdigest()


def utc(value):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def mail_settings():
    key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("RECOVERY_FROM_EMAIL", "").strip()
    origin = os.getenv("RECOVERY_ORIGIN", os.getenv("RENDER_EXTERNAL_URL", "")).strip().rstrip("/")
    parsed = urlsplit(origin)
    if key and sender and parsed.scheme == "https" and parsed.hostname and parsed.path == "" and not (
        parsed.username or parsed.password or parsed.query or parsed.fragment
    ):
        return key, sender, origin
    return None


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
    key, sender, origin = settings
    link = f"{origin}/#reset-password/{code}"
    response = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "from": sender, "to": [email], "subject": "CivicAI Bangladesh password reset",
            "text": (
                "CivicAI Bangladesh-এর পাসওয়ার্ড বদলাতে এই লিংকটি খুলুন। লিংকটি ২০ মিনিট কার্যকর।\n"
                f"{link}\n\n"
                "Use this link to set a new CivicAI Bangladesh password. It expires in 20 minutes. "
                "If you did not request a reset, you can ignore this message.\n"
            ),
        },
        timeout=8.0,
    )
    response.raise_for_status()


def deliver_email_reset(email, settings):
    code = secrets.token_urlsafe(32)
    code_hash = digest(code)
    now = datetime.now(timezone.utc)
    try:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email, User.role == "citizen").with_for_update())
            if user is None:
                return
            existing = db.get(PasswordRecoveryGrant, (user.id, "email"))
            if existing and utc(existing.expires_at) > now:
                return
            replace_grant(db, user.id, "email", code_hash, now + EMAIL_LIFETIME)
            db.commit()
        try:
            send_recovery_email(settings, email, code)
        except httpx.HTTPError as error:
            logger.warning("Recovery email delivery failed (%s)", type(error).__name__)
            with SessionLocal() as db:
                db.execute(delete(PasswordRecoveryGrant).where(PasswordRecoveryGrant.digest == code_hash))
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
    db.execute(delete(PasswordRecoveryGrant).where(PasswordRecoveryGrant.user_id == user_id))
    db.execute(delete(LoginSession).where(LoginSession.user_id == user_id))


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
    user.password_hash = guarded_password_operation(hasher.hash, data.password)
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
