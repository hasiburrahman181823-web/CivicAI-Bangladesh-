"""
CivicAI Bangladesh - Pydantic Request & Response Schemas
Type-safe data validation for all citizen, guest, and administrative workflows.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ----------------- Auth Schemas -----------------
class UserRegisterRequest(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    password: str

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserProfileResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str]
    full_name: str
    role: str
    department: Optional[str]
    created_at: datetime

# ----------------- Complaint Submission Schemas -----------------
class ComplaintCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=15)
    category: Optional[str] = None # Optional: user can pick or leave to AI
    division: str
    district: str
    upazila: str
    area_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_urls: Optional[List[str]] = []
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_anonymous: bool = False
    # Anti-bot honeypot field (must remain empty for human requests)
    website_url_hp: Optional[str] = None

class ComplaintPreviewRequest(BaseModel):
    title: str
    description: str
    division: Optional[str] = None
    district: Optional[str] = None

# ----------------- Complaint Response Schemas -----------------
class TimelineItemResponse(BaseModel):
    id: int
    status: str
    title: str
    description: Optional[str]
    performed_by: str
    created_at: datetime

class CommentItemResponse(BaseModel):
    id: int
    author_name: str
    comment_text: str
    is_official_response: bool
    created_at: datetime

class ComplaintListItemResponse(BaseModel):
    id: int
    tracking_id: str
    title: str
    description: str
    category: str
    severity: str
    status: str
    division: str
    district: str
    upazila: str
    area_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    ai_priority_score: float
    ai_priority_level: str
    upvotes_count: int
    comments_count: int
    image_urls: List[str]
    created_at: datetime
    assigned_department: Optional[str]

class ComplaintDetailResponse(BaseModel):
    id: int
    tracking_id: str
    title: str
    description: str
    category: str
    severity: str
    status: str
    is_guest: bool
    is_anonymous: bool
    division: str
    district: str
    upazila: str
    area_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    assigned_department: Optional[str]
    assigned_officer: Optional[str]
    sla_deadline: Optional[datetime]
    # AI Analysis
    ai_category: Optional[str]
    ai_category_confidence: Optional[float]
    ai_severity: Optional[str]
    ai_severity_confidence: Optional[float]
    ai_priority_score: float
    ai_priority_level: str
    ai_urgency_score: float
    ai_urgency_keywords: List[str]
    ai_explanation_en: Optional[str]
    ai_explanation_bn: Optional[str]
    admin_override: bool
    admin_override_reason: Optional[str]
    # Citizen engagement
    upvotes_count: int
    comments_count: int
    # Media & resolution evidence
    image_urls: List[str]
    resolution_notes: Optional[str]
    resolution_image_urls: List[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    # Nested timeline and comments
    timeline: List[TimelineItemResponse]
    comments: List[CommentItemResponse]

# ----------------- Comment & Upvote Schemas -----------------
class CommentCreateRequest(BaseModel):
    comment_text: str = Field(..., min_length=2, max_length=2000)
    author_name: Optional[str] = "Citizen"

class UpvoteResponse(BaseModel):
    complaint_id: int
    upvotes_count: int
    has_upvoted: bool

# ----------------- Administrative Schemas -----------------
class AdminVerifyRequest(BaseModel):
    verified_category: Optional[str] = None
    verified_severity: Optional[str] = None
    override_reason: Optional[str] = None
    assigned_department: Optional[str] = None

class AdminAssignRequest(BaseModel):
    assigned_department: str
    assigned_officer: Optional[str] = None
    sla_hours: Optional[int] = 48

class AdminStatusUpdateRequest(BaseModel):
    status: str # 'In_Progress', 'Resolved', 'Rejected', etc.
    notes: Optional[str] = None
    resolution_image_urls: Optional[List[str]] = []

class AdminMergeDuplicateRequest(BaseModel):
    primary_complaint_id: int
    duplicate_complaint_id: int
    merge_reason: Optional[str] = "Identical civic issue reported by multiple citizens in same locality"

class AdminStatsOverviewResponse(BaseModel):
    total_complaints: int
    pending_complaints: int
    verified_complaints: int
    in_progress_complaints: int
    resolved_complaints: int
    critical_complaints: int
    resolution_rate_percent: float
    avg_priority_score: float
    category_distribution: Dict[str, int]
    division_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
