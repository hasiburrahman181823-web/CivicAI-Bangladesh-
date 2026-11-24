from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, DateTime, JSON, ForeignKey, LargeBinary, Index
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


class ComplaintIntake(Base):
    __tablename__ = "complaint_intake"
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True)
    sealed_data: Mapped[bytes] = mapped_column(LargeBinary)
    mobile_last4: Mapped[str | None] = mapped_column(String(4))
    mobile_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = (Index("ix_ticket_messages_complaint_order", "complaint_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author_role: Mapped[str] = mapped_column(String(16))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TicketEvent(Base):
    __tablename__ = "ticket_events"
    __table_args__ = (Index("ix_ticket_events_complaint_order", "complaint_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TicketEvidence(Base):
    __tablename__ = "ticket_evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), index=True)
    image: Mapped[bytes] = mapped_column(LargeBinary)
    size: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

class Audit(Base):
    __tablename__ = 'audits'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    complaint_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AdminExportAudit(Base):
    __tablename__ = "admin_export_audits"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    count: Mapped[int]
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
