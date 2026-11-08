"""
CivicAI Bangladesh - Security, Authentication, & Cryptography Module
Directly uses modern bcrypt and PyJWT for secure password hashing and token generation.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
import bcrypt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "civicai-super-secret-key-bd-2026-production-grade")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# In-memory IP rate limiter for guest submissions
IP_REQUEST_LOG: Dict[str, list] = {}
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("GUEST_SUBMISSION_RATE_LIMIT", "15"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "3600")) # 1 hour

def hash_password(password: str) -> str:
    """Securely hash a plaintext password with direct modern bcrypt."""
    # Bcrypt supports max 72 bytes
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate signed JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def check_ip_rate_limit(ip_address: str) -> bool:
    """Sliding-window IP rate limiter."""
    now = time.time()
    if ip_address not in IP_REQUEST_LOG:
        IP_REQUEST_LOG[ip_address] = [now]
        return True

    recent = [t for t in IP_REQUEST_LOG[ip_address] if now - t < RATE_LIMIT_WINDOW]
    if len(recent) >= RATE_LIMIT_MAX_REQUESTS:
        IP_REQUEST_LOG[ip_address] = recent
        return False

    recent.append(now)
    IP_REQUEST_LOG[ip_address] = recent
    return True

def verify_honeypot(honeypot_field_value: Optional[str]) -> bool:
    """Honeypot bot verification."""
    if honeypot_field_value and len(honeypot_field_value.strip()) > 0:
        return False
    return True
