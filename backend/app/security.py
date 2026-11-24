"""Request boundaries and signed, revocable login sessions."""
import base64
import hashlib
import hmac
import secrets
import time
import anyio
import bcrypt
import jwt
from collections import OrderedDict, deque
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from threading import BoundedSemaphore, Lock
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import HTTPException, Request
from sqlalchemy import delete
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import JSONResponse

from .config import CORS_ORIGINS, JWT_SECRET, PRODUCTION, REDIS_URL, TRUSTED_PROXY_NETWORKS
from .models import LoginSession, User

COOKIE = "__Host-civicai" if PRODUCTION else "civicai_session"
SESSION_ISSUER = "civicai-bangladesh"
SESSION_AUDIENCE = "civicai-web"
limits = OrderedDict()
limit_lock = Lock()
redis_client = None
password_slots = BoundedSemaphore(2)


class AccountPasswordHasher:
    prefix = "bcrypt-sha256:"

    def __init__(self):
        self.legacy = PasswordHasher()

    @staticmethod
    def bcrypt_input(password):
        digest = hashlib.sha256(b"CivicAI account password\x00" + password.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def hash(self, password):
        return self.prefix + bcrypt.hashpw(self.bcrypt_input(password), bcrypt.gensalt(rounds=12)).decode()

    def verify(self, stored, password):
        if stored.startswith("$argon2"):
            return self.legacy.verify(stored, password)
        if stored.startswith(self.prefix):
            try:
                if bcrypt.checkpw(self.bcrypt_input(password), stored[len(self.prefix):].encode()):
                    return True
            except ValueError:
                pass
        raise VerificationError("Invalid password")


hasher = AccountPasswordHasher()


def guarded_password_operation(function, *args):
    if not password_slots.acquire(blocking=False):
        raise HTTPException(429, "Authentication is busy. Please try again.")
    try:
        return function(*args)
    finally:
        password_slots.release()

def configure_limit_store():
    global redis_client
    if REDIS_URL:
        import redis
        redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=1.0, socket_connect_timeout=1.0)
        redis_client.ping()

def client_address(request):
    try:
        peer = ip_address(request.client.host) if request.client else None
    except ValueError:
        return None
    if peer is None:
        return None
    if not any(peer in network for network in TRUSTED_PROXY_NETWORKS):
        return str(peer)
    headers = request.headers.getlist("x-forwarded-for")
    if sum(map(len, headers)) > 1024:
        return str(peer)
    for entry in reversed(",".join(headers).split(",")):
        try:
            address = ip_address(entry.strip())
        except ValueError:
            return str(peer)
        if not any(address in network for network in TRUSTED_PROXY_NETWORKS):
            return str(address)
    return str(peer)


def throttle(request: Request, action: str, maximum: int, identity: str | None = None):
    client = identity if identity is not None else client_address(request) or "unknown"
    name = hmac.new(JWT_SECRET.encode(), f"{action}:{client}".encode(), hashlib.sha256).hexdigest()
    if redis_client is not None:
        from redis.exceptions import RedisError
        try:
            count = redis_client.eval(
                "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],60) end; return n",
                1, "civicai:limit:" + name,
            )
        except RedisError as error:
            raise HTTPException(503, "Rate control is temporarily unavailable") from error
        if count > maximum:
            raise HTTPException(429, "Too many requests. Please wait a minute.", headers={"Retry-After":"60"})
        return
    now = time.monotonic()
    with limit_lock:
        while limits and next(iter(limits.values()))[-1] <= now - 60:
            limits.popitem(last=False)
        if name not in limits and len(limits) >= 10000:
            raise HTTPException(503, "Rate control is at capacity")
        bucket = limits.setdefault(name, deque())
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= maximum:
            raise HTTPException(429, "Too many requests. Please wait a minute.", headers={"Retry-After":"60"})
        bucket.append(now)
        limits.move_to_end(name)

def session_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def issue_session(db, user, response, prior_token=None):
    seconds = 900 if user.role == "admin" else 3600
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(seconds=seconds)
    token = jwt.encode(
        {"iss": SESSION_ISSUER, "aud": SESSION_AUDIENCE, "iat": now, "exp": expires_at,
         "jti": secrets.token_urlsafe(32)},
        JWT_SECRET,
        algorithm="HS256",
    )
    db.execute(delete(LoginSession).where(LoginSession.expires_at <= now))
    if prior_token:
        db.execute(delete(LoginSession).where(LoginSession.digest == session_digest(prior_token)))
    db.add(LoginSession(digest=session_digest(token), user_id=user.id, expires_at=expires_at))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=seconds, httponly=True, secure=PRODUCTION,
                        samesite="strict", path="/")

def valid_session_token(token):
    if not token or len(token) > 1024 or not token.isascii():
        return False
    # Existing opaque cookies can finish their original, database-bound session.
    if len(token) == 43 and "." not in token:
        return True
    try:
        jwt.decode(
            token, JWT_SECRET, algorithms=["HS256"], issuer=SESSION_ISSUER, audience=SESSION_AUDIENCE,
            options={"require": ["iss", "aud", "iat", "exp", "jti"]},
        )
    except jwt.InvalidTokenError:
        return False
    return True


def get_session(request, db, required=True):
    token = request.cookies.get(COOKIE)
    if valid_session_token(token):
        session = db.get(LoginSession, session_digest(token))
        if session:
            expiry = session.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry > datetime.now(timezone.utc):
                user = db.get(User, session.user_id)
                if user:
                    return user, session
    if not required:
        return None, None
    raise HTTPException(401, "Please sign in again")

CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; media-src 'self' blob:; "
       "base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'")

class RequestProtection:
    def __init__(self, app):
        self.app = app
        self.media_slots = anyio.Semaphore(2)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = Headers(scope=scope)
        path = scope["path"]
        method = scope["method"]
        private = path.startswith("/api/")

        async def secure_send(message):
            if message["type"] == "http.response.start":
                out = MutableHeaders(scope=message)
                out["X-Content-Type-Options"] = "nosniff"
                out["Referrer-Policy"] = "no-referrer"
                out["X-Frame-Options"] = "DENY"
                out["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
                out["Content-Security-Policy"] = CSP
                if private:
                    out["Cache-Control"] = "no-store"
                if PRODUCTION:
                    out["Strict-Transport-Security"] = "max-age=31536000"
            await send(message)

        async def reject(code, detail, extra_headers=None):
            await JSONResponse({"detail":detail},status_code=code,headers=extra_headers)(scope,receive,secure_send)

        if private and method in {"POST","PATCH","PUT","DELETE"}:
            origin = headers.get("origin")
            if origin:
                parsed = urlsplit(origin)
                host = headers.get("host")
                expected_scheme = "https" if PRODUCTION else scope["scheme"]
                same_origin = parsed.netloc == host and parsed.scheme == expected_scheme
                if not same_origin and (PRODUCTION or origin not in CORS_ORIGINS):
                    return await reject(403, "Origin is not allowed")
            if headers.get("sec-fetch-site") == "cross-site":
                return await reject(403, "Cross-site writes are blocked")
            ticket_upload = path.startswith("/api/tickets/") and path.endswith("/evidence")
            media = path.startswith("/api/media/") or ticket_upload
            cap = (2*1024*1024 + 16*1024) if ticket_upload else (9*1024*1024 if media else 24*1024)
            declared = headers.getlist("content-length")
            if declared and (len(declared) != 1 or not declared[0].isascii() or not declared[0].isdigit()
                             or len(declared[0]) > 9 or int(declared[0]) > cap):
                return await reject(413, "Request exceeds the allowed size")
            if media:
                try:
                    throttle(Request(scope), "media", 6)
                except HTTPException as error:
                    return await reject(error.status_code, error.detail, error.headers)
            if media:
                try:
                    self.media_slots.acquire_nowait()
                except anyio.WouldBlock:
                    return await reject(429, "Media upload capacity reached")
            try:
                body = bytearray()
                try:
                    with anyio.fail_after(15):
                        while True:
                            message = await receive()
                            if message["type"] == "http.disconnect":
                                return
                            chunk = message.get("body", b"")
                            if len(body) + len(chunk) > cap:
                                return await reject(413, "Request exceeds the allowed size")
                            body.extend(chunk)
                            if not message.get("more_body", False):
                                break
                except TimeoutError:
                    return await reject(408, "Request upload timed out")
                if declared and int(declared[0]) != len(body):
                    return await reject(400, "Request size does not match Content-Length")
                delivered = False

                async def replay():
                    nonlocal delivered
                    if delivered:
                        return await receive()
                    delivered = True
                    return {"type":"http.request","body":bytes(body),"more_body":False}

                return await self.app(scope,replay,secure_send)
            finally:
                if media:
                    self.media_slots.release()
        return await self.app(scope,receive,secure_send)
