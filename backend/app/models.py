from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(16), default='citizen')

class Complaint(Base):
    __tablename__ = 'complaints'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tracking_hash: Mapped[str] = mapped_column(String(64))
    owner_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    title: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    area: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(16))
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    category: Mapped[str] = mapped_column(String(32))
    priority: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(24), default='Submitted')
    analysis: Mapped[dict] = mapped_column(JSON)
    duplicate_of: Mapped[str | None] = mapped_column(String(36), nullable=True)

class Audit(Base):
    __tablename__ = 'audits'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    complaint_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class LoginSession(Base):
    __tablename__ = "login_sessions"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    mfa_verified: Mapped[bool] = mapped_column(default=False)

class AdminMFA(Base):
    __tablename__ = "admin_mfa"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    secret_encrypted: Mapped[str] = mapped_column(Text)
    last_counter: Mapped[int] = mapped_column(default=-1)


class PasswordRecoveryGrant(Base):
    __tablename__ = "password_recovery_grants"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    method: Mapped[str] = mapped_column(String(16), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
