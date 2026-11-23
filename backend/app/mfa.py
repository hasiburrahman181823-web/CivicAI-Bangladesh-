"""Administrator TOTP enrollment and replay protection."""
import base64
import hashlib
import hmac
import secrets
import struct
import time

from cryptography.fernet import Fernet
from sqlalchemy import update

from .config import ADMIN_MFA_KEY
from .models import AdminMFA

def new_secret():
    return base64.b32encode(secrets.token_bytes(20)).decode()

def encrypt_secret(secret):
    if not ADMIN_MFA_KEY:
        raise RuntimeError("Set ADMIN_MFA_KEY before enrolling an administrator.")
    return Fernet(ADMIN_MFA_KEY.encode()).encrypt(secret.encode()).decode()

def matching_counter(secret, code, at=None):
    if not code or len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    counter = int(time.time() if at is None else at)//30
    key = base64.b32decode(secret)
    for offset in (-1,0,1):
        if counter+offset < 0:
            continue
        digest = hmac.new(key,struct.pack(">Q",counter+offset),hashlib.sha1).digest()
        position = digest[-1]&15
        value = (struct.unpack(">I",digest[position:position+4])[0]&0x7fffffff)%1_000_000
        if hmac.compare_digest(code,f"{value:06d}"):
            return counter+offset
    return None

def verify_once(db, enrollment, code):
    if not ADMIN_MFA_KEY or not code:
        return False
    secret = Fernet(ADMIN_MFA_KEY.encode()).decrypt(enrollment.secret_encrypted.encode()).decode()
    counter = matching_counter(secret,code)
    if counter is None:
        return False
    result = db.execute(update(AdminMFA).where(
        AdminMFA.user_id==enrollment.user_id, AdminMFA.last_counter<counter
    ).values(last_counter=counter))
    return result.rowcount == 1
