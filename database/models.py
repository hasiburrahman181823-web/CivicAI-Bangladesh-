"""
CivicAI Bangladesh - SQLAlchemy Database Models
Covers Users, Complaints, Timeline, Upvotes, Comments, Duplicate Mergers, and Audit Logs.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50), nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="citizen", nullable=False) # 'citizen', 'officer', 'admin'
    department = Column(String(100), nullable=True) # for officers
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    comments = relationship("ComplaintComment", back_populates="user")
    upvotes = relationship("ComplaintUpvote", back_populates="user")

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(32), unique=True, index=True, nullable=False) # e.g. BD-2026-X8F4K2
    access_pin = Column(String(64), nullable=True) # hashed pin for guest verification

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    is_guest = Column(Boolean, default=False, nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_anonymous = Column(Boolean, default=False, nullable=False)

    # Geographic metadata
    division = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    upazila = Column(String(100), nullable=False, index=True)
    area_name = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)

    # Core workflow status
    category = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True) # Critical, High, Medium, Low
    status = Column(String(50), default="Submitted", index=True, nullable=False)
    # Submitted -> AI_Analyzed -> Verified -> Assigned -> In_Progress -> Resolved -> Rejected -> Duplicate_Merged

    assigned_department = Column(String(200), nullable=True)
    assigned_officer = Column(String(200), nullable=True)
    sla_deadline = Column(DateTime, nullable=True)

    # AI Model Intelligence
    ai_category = Column(String(100), nullable=True)
    ai_category_confidence = Column(Float, nullable=True)
    ai_severity = Column(String(50), nullable=True)
    ai_severity_confidence = Column(Float, nullable=True)
    ai_priority_score = Column(Float, default=0.0, index=True, nullable=False)
    ai_priority_level = Column(String(50), default="Medium", nullable=False)
    ai_urgency_score = Column(Float, default=0.0, nullable=False)
    ai_urgency_keywords = Column(Text, nullable=True) # JSON array string
    ai_explanation_en = Column(Text, nullable=True)
    ai_explanation_bn = Column(Text, nullable=True)
    ai_raw_json = Column(Text, nullable=True)

    # Admin verification and overrides
    admin_override = Column(Boolean, default=False, nullable=False)
    admin_override_reason = Column(Text, nullable=True)
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Citizen engagement
    upvotes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)

    # Attachments & Evidence
    image_urls = Column(Text, nullable=True) # JSON array of initial image attachments
    resolution_notes = Column(Text, nullable=True)
    resolution_image_urls = Column(Text, nullable=True) # JSON array of after-resolution photos
    resolved_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    timeline = relationship("ComplaintTimeline", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintTimeline.created_at.asc()")
    comments = relationship("ComplaintComment", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintComment.created_at.asc()")
    upvotes = relationship("ComplaintUpvote", back_populates="complaint", cascade="all, delete-orphan")

class ComplaintTimeline(Base):
    __tablename__ = "complaint_timeline"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    performed_by = Column(String(255), default="System AI", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="timeline")

class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String(255), nullable=False)
    comment_text = Column(Text, nullable=False)
    is_official_response = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="comments")
    user = relationship("User", back_populates="comments")

class ComplaintUpvote(Base):
    __tablename__ = "complaint_upvotes"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_hash = Column(String(64), nullable=False, index=True) # For anonymous/guest upvote deduplication
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="upvotes")
    user = relationship("User", back_populates="upvotes")

class DuplicateCluster(Base):
    __tablename__ = "duplicate_clusters"

    id = Column(Integer, primary_key=True, index=True)
    primary_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    duplicate_complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=True)
    merged_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(100), nullable=False, index=True) # e.g. 'VERIFY_COMPLAINT', 'OVERRIDE_AI', 'ASSIGN_OFFICER'
    entity_type = Column(String(50), nullable=False) # e.g. 'complaint', 'user'
    entity_id = Column(String(100), nullable=True)
    performed_by_id = Column(Integer, nullable=True)
    performed_by_email = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
