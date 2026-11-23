import os
import secrets

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').strip().lower()
JWT_SECRET = os.getenv('JWT_SECRET', '')
if ENVIRONMENT == 'production' and (len(JWT_SECRET) < 32 or JWT_SECRET.lower() in {'change-me', 'secret', 'your-secret-key', 'changeme' } or len(set(JWT_SECRET)) < 8):
    raise RuntimeError('Set a unique JWT_SECRET of at least 32 characters in production.')
JWT_SECRET = JWT_SECRET or secrets.token_urlsafe(48)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./civicai.db').replace('postgres://', 'postgresql+psycopg://', 1)
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://127.0.0.1:5173,http://localhost:5173').split(',')

PRODUCTION = ENVIRONMENT.strip().lower() == "production"
if PRODUCTION and (len(JWT_SECRET) < 32 or not os.getenv("JWT_SECRET")):
    raise RuntimeError("Production requires an explicit JWT_SECRET.")
REDIS_URL = os.getenv("REDIS_URL", "")
ALLOWED_HOSTS = [name.strip() for name in os.getenv(
    "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver" if not PRODUCTION else ""
).split(",") if name.strip()]
CORS_ORIGINS = [x.strip() for x in CORS_ORIGINS if x.strip()]
if PRODUCTION:
    if not ALLOWED_HOSTS or any("*" in host or "/" in host for host in ALLOWED_HOSTS):
        raise RuntimeError("Set exact ALLOWED_HOSTS for production.")
    if any(not origin.startswith("https://") for origin in CORS_ORIGINS):
        raise RuntimeError("Use HTTPS origins or empty CORS_ORIGINS in production.")
    if not REDIS_URL:
        raise RuntimeError("Set REDIS_URL for shared rate controls in production.")
