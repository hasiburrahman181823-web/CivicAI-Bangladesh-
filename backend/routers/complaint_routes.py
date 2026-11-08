"""
CivicAI Bangladesh - Citizen & Guest Complaint Management Routes
Handles guest submission with bot protection, registered citizen reporting,
tracking, public feed, interactive map endpoints, upvotes, and comments.
"""

import json
import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.connection import get_db
from database.models import (
    Complaint, ComplaintTimeline, ComplaintComment, ComplaintUpvote, User
)
from backend.security import (
    verify_honeypot, check_ip_rate_limit, hash_password, verify_password
)
from backend.schemas import (
    ComplaintCreateRequest, ComplaintPreviewRequest,
    ComplaintListItemResponse, ComplaintDetailResponse,
    CommentCreateRequest, UpvoteResponse
)
from backend.routers.auth_routes import get_current_user
from backend.websocket_manager import ws_manager
from ai.pipeline import ComplaintIntelligenceEngine

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

# Bangladesh administrative structure for frontend dropdowns
BANGLADESH_DIVISIONS_DATA = {
    "Dhaka": {
        "districts": {
            "Dhaka": ["Mirpur", "Dhanmondi", "Gulshan", "Mohammadpur", "Uttara", "Badda", "Tejgaon", "Jatrabari", "Lalbagh", "Motijheel", "Keraniganj", "Savar", "Dhamrai"],
            "Gazipur": ["Gazipur Sadar", "Tongi", "Kaliakair", "Sreepur", "Kapasia", "Kaliganj"],
            "Narayanganj": ["Narayanganj Sadar", "Bandar", "Fatullah", "Siddhirganj", "Rupganj", "Araihazar", "Sonargaon"],
            "Tangail": ["Tangail Sadar", "Mirzapur", "Madhupur", "Ghatail", "Kalihati", "Sakhipur"],
            "Narsingdi": ["Narsingdi Sadar", "Palash", "Shibpur", "Raipura", "Belabo", "Monohardi"],
            "Faridpur": ["Faridpur Sadar", "Bhanga", "Boalmari", "Madhukhali", "Nagarkanda"]
        }
    },
    "Chattogram": {
        "districts": {
            "Chattogram": ["Kotwali", "Panchlaish", "Pahartali", "Double Mooring", "Halishahar", "Chandgaon", "Bakalia", "Patenga", "Hathazari", "Sitakunda", "Patiya"],
            "Cox's Bazar": ["Cox's Bazar Sadar", "Ramu", "Teknaf", "Ukhia", "Chakaria", "Pekua", "Maheshkhali"],
            "Cumilla": ["Cumilla Sadar", "Barura", "Brahmanpara", "Burichang", "Chandina", "Chauddagram", "Daudkandi", "Debidwar", "Homna", "Laksam"],
            "Feni": ["Feni Sadar", "Chhagalnaiya", "Daganbhuiyan", "Parshuram", "Fulgazi", "Sonagazi"],
            "Brahmanbaria": ["Brahmanbaria Sadar", "Ashuganj", "Bancharampur", "Kasba", "Nabinagar", "Sarail"],
            "Noakhali": ["Noakhali Sadar", "Begumganj", "Chatkhil", "Companiganj", "Hatiya", "Senbagh"]
        }
    },
    "Rajshahi": {
        "districts": {
            "Rajshahi": ["Boalia", "Rajpara", "Motihar", "Shah Makhdum", "Paba", "Bagha", "Charghat", "Durgapur", "Godagari", "Tanore"],
            "Bogura": ["Bogura Sadar", "Adamdighi", "Dhunat", "Dhupchanchia", "Gabtali", "Kahaloo", "Nandigram", "Sariakandi", "Shajahanpur", "Sherpur", "Shibganj", "Sonatala"],
            "Pabna": ["Pabna Sadar", "Atgharia", "Bera", "Bhangura", "Chatmohar", "Faridpur", "Ishwardi", "Santhia", "Sujanagar"],
            "Naogaon": ["Naogaon Sadar", "Atrai", "Badalgachhi", "Dhamoirhat", "Manda", "Mohadevpur", "Niamatpur", "Patnitala", "Porsha", "Raninagar", "Sapahar"],
            "Sirajganj": ["Sirajganj Sadar", "Belkuchi", "Chauhali", "Kamarkhanda", "Kazipur", "Rayganj", "Shahjadpur", "Tarash", "Ullapara"]
        }
    },
    "Khulna": {
        "districts": {
            "Khulna": ["Khulna Sadar", "Sonadanga", "Khalishpur", "Daulatpur", "Khan Jahan Ali", "Batiaghata", "Dacope", "Dumuria", "Dighalia", "Koyra", "Paikgachha", "Phultala", "Rupsha", "Terokhada"],
            "Jashore": ["Jashore Sadar", "Abhaynagar", "Bagherpara", "Chaugachha", "Jhikargachha", "Keshabpur", "Manirampur", "Sharsha"],
            "Kushtia": ["Kushtia Sadar", "Bheramara", "Daulatpur", "Khoksa", "Kumarkhali", "Mirpur"],
            "Satkhira": ["Satkhira Sadar", "Assasuni", "Debhata", "Kalaroa", "Kaliganj", "Shyamnagar", "Tala"],
            "Bagerhat": ["Bagerhat Sadar", "Chitalmari", "Fakirhat", "Kachua", "Mollahat", "Mongla", "Morrelganj", "Rampal", "Sarankhola"]
        }
    },
    "Barishal": {
        "districts": {
            "Barishal": ["Barishal Sadar", "Bakerganj", "Babuganj", "Banaripara", "Gournadi", "Hizla", "Mehendiganj", "Muladi", "Wazirpur"],
            "Patuakhali": ["Patuakhali Sadar", "Bauphal", "Dashmina", "Galachipa", "Kalapara", "Mirzaganj", "Rangabali", "Dumki"],
            "Bhola": ["Bhola Sadar", "Burhanuddin", "Char Fasson", "Daulatkhan", "Lalmohan", "Manpura", "Tazumuddin"],
            "Pirojpur": ["Pirojpur Sadar", "Bhandaria", "Kawkhali", "Mathbaria", "Nazirpur", "Nesarabad", "Zianagar"]
        }
    },
    "Sylhet": {
        "districts": {
            "Sylhet": ["Sylhet Sadar", "South Surma", "Beanibazar", "Golapganj", "Biswanath", "Fenchuganj", "Balaganj", "Companiganj", "Gowainghat", "Jaintiapur", "Kanaighat", "Zakiganj"],
            "Moulvibazar": ["Moulvibazar Sadar", "Barlekha", "Juri", "Kamalganj", "Kulaura", "Rajnagar", "Sreemangal"],
            "Habiganj": ["Habiganj Sadar", "Ajmiriganj", "Bahubal", "Baniachang", "Chunarughat", "Lakhai", "Madhabpur", "Nabiganj"],
            "Sunamganj": ["Sunamganj Sadar", "Bishwamvarpur", "Chhatak", "Derai", "Dharampasha", "Dowarabazar", "Jagannathpur", "Jamalganj", "Sullah", "Tahirpur"]
        }
    },
    "Rangpur": {
        "districts": {
            "Rangpur": ["Rangpur Sadar", "Kotwali", "Badarganj", "Gangachhara", "Kaunia", "Mithapukur", "Pirgachha", "Pirganj", "Taraganj"],
            "Dinajpur": ["Dinajpur Sadar", "Birganj", "Birampur", "Biral", "Bochaganj", "Chirirbandar", "Fulbari", "Ghoraghat", "Hakimpur", "Kaharole", "Khansama", "Nawabganj", "Parbatipur"],
            "Kurigram": ["Kurigram Sadar", "Bhurungamari", "Char Rajibpur", "Chilmari", "Nageshwari", "Phulbari", "Rajarhat", "Raomari", "Ulipur"],
            "Gaibandha": ["Gaibandha Sadar", "Fulchhari", "Gobindaganj", "Palashbari", "Sadullapur", "Saghata", "Sundarganj"]
        }
    },
    "Mymensingh": {
        "districts": {
            "Mymensingh": ["Mymensingh Sadar", "Trishal", "Muktagachha", "Bhaluka", "Gafargaon", "Gauripur", "Haluaghat", "Ishwarganj", "Dhobaura", "Nandail", "Phulpur", "Tara Khanda"],
            "Jamalpur": ["Jamalpur Sadar", "Bakshiganj", "Dewanganj", "Islampur", "Madarganj", "Melandaha", "Sarishabari"],
            "Netrokona": ["Netrokona Sadar", "Atpara", "Barhatta", "Durgapur", "Khaliajuri", "Kalmakanda", "Kendua", "Madan", "Mohanganj", "Purbadhala"],
            "Sherpur": ["Sherpur Sadar", "Jhenaigati", "Nakla", "Nalitabari", "Sreebardi"]
        }
    }
}

def generate_tracking_id() -> str:
    """Generate high-entropy unique tracking ID for citizens, e.g., BD-2026-X8F4K2."""
    chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    random_part = "".join(random.choice(chars) for _ in range(6))
    return f"BD-2026-{random_part}"

def get_client_ip(request: Request) -> str:
    """Extract real client IP considering forward headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"

@router.get("/divisions")
def get_divisions():
    """Return complete hierarchical Bangladesh administrative boundaries."""
    return BANGLADESH_DIVISIONS_DATA

@router.post("/preview")
def preview_complaint_ai(req: ComplaintPreviewRequest, db: Session = Depends(get_db)):
    """
    Real-time interactive AI assistance for citizen submission form.
    Provides instant category, severity, urgency, priority preview and detects similar issues nearby.
    """
    engine = ComplaintIntelligenceEngine.get_instance()

    # Fetch recent complaints for real-time duplicate checking
    recent = db.query(Complaint).order_by(desc(Complaint.created_at)).limit(30).all()
    recent_dicts = [
        {
            "id": c.id,
            "tracking_id": c.tracking_id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "severity": c.severity,
            "status": c.status,
            "latitude": c.latitude,
            "longitude": c.longitude
        }
        for c in recent
    ]

    analysis = engine.analyze_complaint(
        title=req.title,
        description=req.description,
        existing_complaints=recent_dicts
    )

    return {
        "language": analysis["language"],
        "predicted_category": analysis["category"],
        "category_confidence": analysis["category_confidence"],
        "top_categories": analysis["top_categories"],
        "predicted_severity": analysis["severity"],
        "severity_confidence": analysis["severity_confidence"],
        "top_severities": analysis["top_severities"],
        "urgency_score": analysis["urgency_score"],
        "urgency_keywords": analysis["urgency_keywords"],
        "estimated_priority_score": analysis["priority_score"],
        "priority_level": analysis["priority_level"],
        "potential_duplicates": analysis["duplicates"][:3],
        "is_duplicate_flagged": analysis["is_duplicate_flagged"],
        "recommended_department": analysis["explanation"]["recommended_department"],
        "recommended_department_bn": analysis["explanation"]["recommended_department_bn"]
    }

@router.post("/guest", status_code=status.HTTP_201_CREATED)
async def submit_guest_complaint(
    req: ComplaintCreateRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Public Guest Complaint Submission (No Login Required).
    Protected with Anti-Bot Honeypot and Sliding-Window IP Rate Limiting.
    Returns secure tracking ID and guest access PIN.
    """
    # 1. Anti-bot honeypot check
    if not verify_honeypot(req.website_url_hp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automated submission detected. Honeypot check failed."
        )

    # 2. IP Rate Limiting
    client_ip = get_client_ip(request)
    if not check_ip_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Submission rate limit exceeded from your network. Please wait a few minutes."
        )

    # 3. Initialize AI pipeline and fetch existing complaints for duplicate detection
    engine = ComplaintIntelligenceEngine.get_instance()
    recent = db.query(Complaint).order_by(desc(Complaint.created_at)).limit(50).all()
    recent_dicts = [
        {
            "id": c.id,
            "tracking_id": c.tracking_id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "severity": c.severity,
            "status": c.status,
            "latitude": c.latitude,
            "longitude": c.longitude
        }
        for c in recent
    ]

    # Run genuine multi-model AI analysis
    ai_res = engine.analyze_complaint(
        title=req.title,
        description=req.description,
        latitude=req.latitude,
        longitude=req.longitude,
        existing_complaints=recent_dicts
    )

    # Determine final category and severity (use user selected if specified, else AI prediction)
    final_category = req.category if req.category else ai_res["category"]
    final_severity = ai_res["severity"]

    # Generate unique Tracking ID and 6-digit access PIN
    tracking_id = generate_tracking_id()
    raw_pin = f"{random.randint(100000, 999999)}"
    now = datetime.utcnow()

    complaint = Complaint(
        tracking_id=tracking_id,
        access_pin=hash_password(raw_pin),
        title=req.title.strip(),
        description=req.description.strip(),
        is_guest=True,
        citizen_id=None,
        contact_email=req.contact_email.strip() if req.contact_email else None,
        contact_phone=req.contact_phone.strip() if req.contact_phone else None,
        is_anonymous=req.is_anonymous,
        division=req.division,
        district=req.district,
        upazila=req.upazila,
        area_name=req.area_name.strip() if req.area_name else None,
        latitude=req.latitude,
        longitude=req.longitude,
        category=final_category,
        severity=final_severity,
        status="AI_Analyzed",
        assigned_department=ai_res["explanation"]["recommended_department"],
        sla_deadline=now + timedelta(hours=ai_res["explanation"]["recommended_sla_hours"]),
        # AI Intelligence
        ai_category=ai_res["category"],
        ai_category_confidence=ai_res["category_confidence"],
        ai_severity=ai_res["severity"],
        ai_severity_confidence=ai_res["severity_confidence"],
        ai_priority_score=ai_res["priority_score"],
        ai_priority_level=ai_res["priority_level"],
        ai_urgency_score=ai_res["urgency_score"],
        ai_urgency_keywords=json.dumps(ai_res["urgency_keywords"], ensure_ascii=False),
        ai_explanation_en=ai_res["explanation"]["summary_en"],
        ai_explanation_bn=ai_res["explanation"]["summary_bn"],
        ai_raw_json=json.dumps(ai_res, ensure_ascii=False),
        image_urls=json.dumps(req.image_urls or []),
        created_at=now,
        updated_at=now
    )
    db.add(complaint)
    db.flush()

    # Create initial timeline milestones
    t1 = ComplaintTimeline(
        complaint_id=complaint.id,
        status="Submitted",
        title="Public Guest Complaint Received",
        description=f"Complaint securely registered via Anonymous Guest Mode from {req.upazila}, {req.district}.",
        performed_by="Guest Citizen",
        created_at=now
    )
    t2 = ComplaintTimeline(
        complaint_id=complaint.id,
        status="AI_Analyzed",
        title="AI Multilingual Intelligence Analysis",
        description=(
            f"AI Pipeline classified complaint as '{ai_res['category']}' ({int(ai_res['category_confidence']*100)}% conf) "
            f"with '{ai_res['severity']}' severity. Calculated Priority Index: {ai_res['priority_score']}/100 ({ai_res['priority_level']})."
        ),
        performed_by="CivicAI Bangladesh Engine",
        created_at=now + timedelta(seconds=2)
    )
    db.add_all([t1, t2])
    db.commit()
    db.refresh(complaint)

    # Broadcast event via WebSocket
    await ws_manager.broadcast_event("NEW_COMPLAINT", {
        "id": complaint.id,
        "tracking_id": complaint.tracking_id,
        "title": complaint.title,
        "category": complaint.category,
        "severity": complaint.severity,
        "status": complaint.status,
        "division": complaint.division,
        "district": complaint.district,
        "upazila": complaint.upazila,
        "ai_priority_score": complaint.ai_priority_score,
        "ai_priority_level": complaint.ai_priority_level,
        "created_at": complaint.created_at.isoformat()
    })

    return {
        "success": True,
        "tracking_id": tracking_id,
        "access_pin": raw_pin,
        "message": "Complaint successfully submitted and analyzed by AI.",
        "category": complaint.category,
        "severity": complaint.severity,
        "priority_score": complaint.ai_priority_score,
        "priority_level": complaint.ai_priority_level,
        "recommended_department": ai_res["explanation"]["recommended_department"],
        "duplicates_detected": len(ai_res["duplicates"])
    }

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_authenticated_complaint(
    req: ComplaintCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Authenticated Citizen Complaint Submission.
    Linked to citizen account for personal dashboard tracking.
    """
    engine = ComplaintIntelligenceEngine.get_instance()
    recent = db.query(Complaint).order_by(desc(Complaint.created_at)).limit(50).all()
    recent_dicts = [
        {
            "id": c.id,
            "tracking_id": c.tracking_id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "severity": c.severity,
            "status": c.status,
            "latitude": c.latitude,
            "longitude": c.longitude
        }
        for c in recent
    ]

    ai_res = engine.analyze_complaint(
        title=req.title,
        description=req.description,
        latitude=req.latitude,
        longitude=req.longitude,
        existing_complaints=recent_dicts
    )

    final_category = req.category if req.category else ai_res["category"]
    final_severity = ai_res["severity"]
    tracking_id = generate_tracking_id()
    now = datetime.utcnow()

    complaint = Complaint(
        tracking_id=tracking_id,
        access_pin=None,
        title=req.title.strip(),
        description=req.description.strip(),
        is_guest=False,
        citizen_id=current_user.id,
        contact_email=current_user.email,
        contact_phone=current_user.phone or req.contact_phone,
        is_anonymous=req.is_anonymous,
        division=req.division,
        district=req.district,
        upazila=req.upazila,
        area_name=req.area_name.strip() if req.area_name else None,
        latitude=req.latitude,
        longitude=req.longitude,
        category=final_category,
        severity=final_severity,
        status="AI_Analyzed",
        assigned_department=ai_res["explanation"]["recommended_department"],
        sla_deadline=now + timedelta(hours=ai_res["explanation"]["recommended_sla_hours"]),
        ai_category=ai_res["category"],
        ai_category_confidence=ai_res["category_confidence"],
        ai_severity=ai_res["severity"],
        ai_severity_confidence=ai_res["severity_confidence"],
        ai_priority_score=ai_res["priority_score"],
        ai_priority_level=ai_res["priority_level"],
        ai_urgency_score=ai_res["urgency_score"],
        ai_urgency_keywords=json.dumps(ai_res["urgency_keywords"], ensure_ascii=False),
        ai_explanation_en=ai_res["explanation"]["summary_en"],
        ai_explanation_bn=ai_res["explanation"]["summary_bn"],
        ai_raw_json=json.dumps(ai_res, ensure_ascii=False),
        image_urls=json.dumps(req.image_urls or []),
        created_at=now,
        updated_at=now
    )
    db.add(complaint)
    db.flush()

    t1 = ComplaintTimeline(
        complaint_id=complaint.id,
        status="Submitted",
        title="Citizen Complaint Registered",
        description=f"Registered by verified citizen ({current_user.full_name}) in {req.upazila}, {req.district}.",
        performed_by="Verified Citizen",
        created_at=now
    )
    t2 = ComplaintTimeline(
        complaint_id=complaint.id,
        status="AI_Analyzed",
        title="AI Multilingual Intelligence Analysis",
        description=f"AI classified issue as '{ai_res['category']}' ({int(ai_res['category_confidence']*100)}% conf). Priority Score: {ai_res['priority_score']}/100.",
        performed_by="CivicAI Bangladesh Engine",
        created_at=now + timedelta(seconds=2)
    )
    db.add_all([t1, t2])
    db.commit()
    db.refresh(complaint)

    await ws_manager.broadcast_event("NEW_COMPLAINT", {
        "id": complaint.id,
        "tracking_id": complaint.tracking_id,
        "title": complaint.title,
        "category": complaint.category,
        "severity": complaint.severity,
        "status": complaint.status,
        "division": complaint.division,
        "district": complaint.district,
        "upazila": complaint.upazila,
        "ai_priority_score": complaint.ai_priority_score,
        "ai_priority_level": complaint.ai_priority_level,
        "created_at": complaint.created_at.isoformat()
    })

    return {
        "success": True,
        "tracking_id": tracking_id,
        "message": "Complaint successfully submitted.",
        "category": complaint.category,
        "severity": complaint.severity,
        "priority_score": complaint.ai_priority_score,
        "priority_level": complaint.ai_priority_level
    }

@router.get("/track/{tracking_id}")
def track_complaint(tracking_id: str, db: Session = Depends(get_db)):
    """
    Public Complaint Tracking Portal (No Login Required).
    Allows citizens to track complaint status, milestones, department assignment, and resolution.
    """
    comp = db.query(Complaint).filter(Complaint.tracking_id == tracking_id.strip()).first()
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No complaint found with Tracking ID '{tracking_id}'"
        )

    # Calculate status percentage
    status_order = {
        "Submitted": 15,
        "AI_Analyzed": 30,
        "Verified": 50,
        "Assigned": 65,
        "In_Progress": 80,
        "Resolved": 100,
        "Rejected": 100,
        "Duplicate_Merged": 100
    }
    progress_percent = status_order.get(comp.status, 25)

    timeline_items = [
        {
            "id": t.id,
            "status": t.status,
            "title": t.title,
            "description": t.description,
            "performed_by": t.performed_by,
            "created_at": t.created_at
        }
        for t in comp.timeline
    ]

    return {
        "tracking_id": comp.tracking_id,
        "title": comp.title,
        "description": comp.description,
        "category": comp.category,
        "severity": comp.severity,
        "status": comp.status,
        "progress_percent": progress_percent,
        "division": comp.division,
        "district": comp.district,
        "upazila": comp.upazila,
        "area_name": comp.area_name,
        "assigned_department": comp.assigned_department,
        "assigned_officer": comp.assigned_officer if comp.assigned_officer else "Field Unit Officer",
        "sla_deadline": comp.sla_deadline,
        "ai_priority_score": comp.ai_priority_score,
        "ai_priority_level": comp.ai_priority_level,
        "ai_explanation_en": comp.ai_explanation_en,
        "ai_explanation_bn": comp.ai_explanation_bn,
        "upvotes_count": comp.upvotes_count,
        "comments_count": comp.comments_count,
        "image_urls": json.loads(comp.image_urls) if comp.image_urls else [],
        "resolution_notes": comp.resolution_notes,
        "resolution_image_urls": json.loads(comp.resolution_image_urls) if comp.resolution_image_urls else [],
        "resolved_at": comp.resolved_at,
        "created_at": comp.created_at,
        "updated_at": comp.updated_at,
        "timeline": timeline_items
    }

@router.get("/feed", response_model=List[ComplaintListItemResponse])
def get_complaint_feed(
    search: Optional[str] = None,
    division: Optional[str] = None,
    district: Optional[str] = None,
    upazila: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    sort_by: Optional[str] = "priority", # 'priority', 'date', 'upvotes'
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Searchable, filterable public complaints feed.
    Supports filtering by Bangladesh division, district, category, severity, and status.
    """
    query = db.query(Complaint)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (Complaint.title.ilike(search_term)) |
            (Complaint.description.ilike(search_term)) |
            (Complaint.area_name.ilike(search_term)) |
            (Complaint.tracking_id.ilike(search_term))
        )

    if division and division != "All":
        query = query.filter(Complaint.division == division)
    if district and district != "All":
        query = query.filter(Complaint.district == district)
    if upazila and upazila != "All":
        query = query.filter(Complaint.upazila == upazila)
    if category and category != "All":
        query = query.filter(Complaint.category == category)
    if severity and severity != "All":
        query = query.filter(Complaint.severity == severity)
    if status_filter and status_filter != "All":
        query = query.filter(Complaint.status == status_filter)

    # Sorting
    if sort_by == "date":
        query = query.order_by(desc(Complaint.created_at))
    elif sort_by == "upvotes":
        query = query.order_by(desc(Complaint.upvotes_count), desc(Complaint.created_at))
    else: # Default priority ranking
        query = query.order_by(desc(Complaint.ai_priority_score), desc(Complaint.created_at))

    results = query.offset(offset).limit(limit).all()

    return [
        ComplaintListItemResponse(
            id=c.id,
            tracking_id=c.tracking_id,
            title=c.title,
            description=c.description[:240] + ("..." if len(c.description) > 240 else ""),
            category=c.category,
            severity=c.severity,
            status=c.status,
            division=c.division,
            district=c.district,
            upazila=c.upazila,
            area_name=c.area_name,
            latitude=c.latitude,
            longitude=c.longitude,
            ai_priority_score=c.ai_priority_score,
            ai_priority_level=c.ai_priority_level,
            upvotes_count=c.upvotes_count,
            comments_count=c.comments_count,
            image_urls=json.loads(c.image_urls) if c.image_urls else [],
            created_at=c.created_at,
            assigned_department=c.assigned_department
        )
        for c in results
    ]

@router.get("/map")
def get_map_markers(
    division: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    """
    Returns geo-coordinate markers for the interactive Leaflet map.
    Only complaints with valid coordinates are returned.
    """
    query = db.query(Complaint).filter(Complaint.latitude.isnot(None), Complaint.longitude.isnot(None))

    if division and division != "All":
        query = query.filter(Complaint.division == division)
    if category and category != "All":
        query = query.filter(Complaint.category == category)
    if severity and severity != "All":
        query = query.filter(Complaint.severity == severity)
    if status_filter and status_filter != "All":
        query = query.filter(Complaint.status == status_filter)

    complaints = query.order_by(desc(Complaint.ai_priority_score)).limit(300).all()

    return [
        {
            "id": c.id,
            "tracking_id": c.tracking_id,
            "title": c.title,
            "category": c.category,
            "severity": c.severity,
            "status": c.status,
            "division": c.division,
            "district": c.district,
            "upazila": c.upazila,
            "area_name": c.area_name,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "ai_priority_score": c.ai_priority_score,
            "ai_priority_level": c.ai_priority_level,
            "upvotes_count": c.upvotes_count,
            "created_at": c.created_at.isoformat(),
            "assigned_department": c.assigned_department
        }
        for c in complaints
    ]

@router.get("/{id}", response_model=ComplaintDetailResponse)
def get_complaint_details(id: int, db: Session = Depends(get_db)):
    """Fetch complete complaint details including timeline and comments."""
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    timeline_items = [
        {
            "id": t.id,
            "status": t.status,
            "title": t.title,
            "description": t.description,
            "performed_by": t.performed_by,
            "created_at": t.created_at
        }
        for t in comp.timeline
    ]

    comments_items = [
        {
            "id": cm.id,
            "author_name": cm.author_name,
            "comment_text": cm.comment_text,
            "is_official_response": cm.is_official_response,
            "created_at": cm.created_at
        }
        for cm in comp.comments
    ]

    keywords = []
    if comp.ai_urgency_keywords:
        try:
            keywords = json.loads(comp.ai_urgency_keywords)
        except Exception:
            keywords = []

    return ComplaintDetailResponse(
        id=comp.id,
        tracking_id=comp.tracking_id,
        title=comp.title,
        description=comp.description,
        category=comp.category,
        severity=comp.severity,
        status=comp.status,
        is_guest=comp.is_guest,
        is_anonymous=comp.is_anonymous,
        division=comp.division,
        district=comp.district,
        upazila=comp.upazila,
        area_name=comp.area_name,
        latitude=comp.latitude,
        longitude=comp.longitude,
        assigned_department=comp.assigned_department,
        assigned_officer=comp.assigned_officer,
        sla_deadline=comp.sla_deadline,
        ai_category=comp.ai_category,
        ai_category_confidence=comp.ai_category_confidence,
        ai_severity=comp.ai_severity,
        ai_severity_confidence=comp.ai_severity_confidence,
        ai_priority_score=comp.ai_priority_score,
        ai_priority_level=comp.ai_priority_level,
        ai_urgency_score=comp.ai_urgency_score,
        ai_urgency_keywords=keywords,
        ai_explanation_en=comp.ai_explanation_en,
        ai_explanation_bn=comp.ai_explanation_bn,
        admin_override=comp.admin_override,
        admin_override_reason=comp.admin_override_reason,
        upvotes_count=comp.upvotes_count,
        comments_count=comp.comments_count,
        image_urls=json.loads(comp.image_urls) if comp.image_urls else [],
        resolution_notes=comp.resolution_notes,
        resolution_image_urls=json.loads(comp.resolution_image_urls) if comp.resolution_image_urls else [],
        resolved_at=comp.resolved_at,
        created_at=comp.created_at,
        updated_at=comp.updated_at,
        timeline=timeline_items,
        comments=comments_items
    )

@router.post("/{id}/upvote", response_model=UpvoteResponse)
async def upvote_complaint(
    id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Citizen/Guest Upvote ('I am also affected by this issue').
    Deduplicates by IP hash and recalculates AI priority score.
    """
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    client_ip = get_client_ip(request)
    ip_hash = hashlib.sha256(client_ip.encode('utf-8')).hexdigest()

    existing_upvote = db.query(ComplaintUpvote).filter(
        ComplaintUpvote.complaint_id == id,
        ComplaintUpvote.ip_hash == ip_hash
    ).first()

    if existing_upvote:
        # Toggle off / Remove upvote
        db.delete(existing_upvote)
        comp.upvotes_count = max(0, comp.upvotes_count - 1)
        has_upvoted = False
    else:
        # Add upvote
        new_upvote = ComplaintUpvote(
            complaint_id=id,
            user_id=None,
            ip_hash=ip_hash
        )
        db.add(new_upvote)
        comp.upvotes_count += 1
        has_upvoted = True

    # Recalculate priority score dynamically with new upvotes
    from ai.priority_scorer import calculate_priority_score
    updated_p = calculate_priority_score(
        severity=comp.severity,
        category=comp.category,
        urgency_score=comp.ai_urgency_score,
        upvotes=comp.upvotes_count
    )
    comp.ai_priority_score = updated_p["priority_score"]
    comp.ai_priority_level = updated_p["priority_level"]

    db.commit()

    # Broadcast upvote event
    await ws_manager.broadcast_event("UPVOTE_UPDATED", {
        "complaint_id": comp.id,
        "upvotes_count": comp.upvotes_count,
        "new_priority_score": comp.ai_priority_score
    })

    return {
        "complaint_id": comp.id,
        "upvotes_count": comp.upvotes_count,
        "has_upvoted": has_upvoted
    }

@router.post("/{id}/comments")
async def add_comment(
    id: int,
    req: CommentCreateRequest,
    db: Session = Depends(get_db)
):
    """Post comment to public discussion timeline."""
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    author = req.author_name.strip() if req.author_name else "Concerned Citizen"
    comment = ComplaintComment(
        complaint_id=id,
        user_id=None,
        author_name=author,
        comment_text=req.comment_text.strip(),
        is_official_response=False,
        created_at=datetime.utcnow()
    )
    db.add(comment)
    comp.comments_count += 1
    db.commit()
    db.refresh(comment)

    await ws_manager.broadcast_event("NEW_COMMENT", {
        "complaint_id": comp.id,
        "author_name": comment.author_name,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at.isoformat()
    })

    return {
        "success": True,
        "comment_id": comment.id,
        "author_name": comment.author_name,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at
    }
