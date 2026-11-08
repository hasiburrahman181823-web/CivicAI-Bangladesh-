"""
CivicAI Bangladesh - Administrative Control Panel Routes
Comprehensive administrative workflow: AI verification, department assignment,
status transitions, duplicate complaint merging, resolution evidence uploads,
model performance monitoring, and audit logging.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from database.connection import get_db
from database.models import (
    Complaint, ComplaintTimeline, ComplaintComment, DuplicateCluster, AuditLog, User
)
from backend.schemas import (
    AdminVerifyRequest, AdminAssignRequest, AdminStatusUpdateRequest,
    AdminMergeDuplicateRequest, AdminStatsOverviewResponse
)
from backend.routers.auth_routes import get_current_admin
from backend.websocket_manager import ws_manager

router = APIRouter(prefix="/api/admin", tags=["Administration"])

@router.get("/stats", response_model=AdminStatsOverviewResponse)
def get_admin_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aggregate executive KPI analytics."""
    total = db.query(Complaint).count()
    pending = db.query(Complaint).filter(Complaint.status.in_(["Submitted", "AI_Analyzed"])).count()
    verified = db.query(Complaint).filter(Complaint.status == "Verified").count()
    in_progress = db.query(Complaint).filter(Complaint.status == "In_Progress").count()
    resolved = db.query(Complaint).filter(Complaint.status == "Resolved").count()
    critical = db.query(Complaint).filter(Complaint.severity == "Critical").count()

    res_rate = round((resolved / total * 100.0), 1) if total > 0 else 0.0

    avg_p = db.query(func.avg(Complaint.ai_priority_score)).scalar() or 0.0

    # Category breakdown
    cat_counts = db.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all()
    cat_dist = {cat: count for cat, count in cat_counts}

    # Division breakdown
    div_counts = db.query(Complaint.division, func.count(Complaint.id)).group_by(Complaint.division).all()
    div_dist = {div: count for div, count in div_counts}

    # Severity breakdown
    sev_counts = db.query(Complaint.severity, func.count(Complaint.id)).group_by(Complaint.severity).all()
    sev_dist = {sev: count for sev, count in sev_counts}

    return AdminStatsOverviewResponse(
        total_complaints=total,
        pending_complaints=pending,
        verified_complaints=verified,
        in_progress_complaints=in_progress,
        resolved_complaints=resolved,
        critical_complaints=critical,
        resolution_rate_percent=res_rate,
        avg_priority_score=round(float(avg_p), 1),
        category_distribution=cat_dist,
        division_distribution=div_dist,
        severity_distribution=sev_dist
    )

@router.get("/complaints")
def list_admin_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    severity: Optional[str] = None,
    division: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Retrieve complaints queue ordered by AI Priority Score."""
    query = db.query(Complaint)

    if status_filter and status_filter != "All":
        query = query.filter(Complaint.status == status_filter)
    if category and category != "All":
        query = query.filter(Complaint.category == category)
    if severity and severity != "All":
        query = query.filter(Complaint.severity == severity)
    if division and division != "All":
        query = query.filter(Complaint.division == division)
    if search:
        st = f"%{search.strip()}%"
        query = query.filter(
            (Complaint.title.ilike(st)) |
            (Complaint.tracking_id.ilike(st)) |
            (Complaint.upazila.ilike(st)) |
            (Complaint.district.ilike(st))
        )

    complaints = query.order_by(desc(Complaint.ai_priority_score), desc(Complaint.created_at)).offset(offset).limit(limit).all()

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
            "assigned_department": c.assigned_department,
            "assigned_officer": c.assigned_officer,
            "ai_priority_score": c.ai_priority_score,
            "ai_priority_level": c.ai_priority_level,
            "ai_category": c.ai_category,
            "ai_category_confidence": c.ai_category_confidence,
            "ai_severity": c.ai_severity,
            "ai_severity_confidence": c.ai_severity_confidence,
            "admin_override": c.admin_override,
            "admin_override_reason": c.admin_override_reason,
            "upvotes_count": c.upvotes_count,
            "comments_count": c.comments_count,
            "sla_deadline": c.sla_deadline,
            "created_at": c.created_at.isoformat()
        }
        for c in complaints
    ]

@router.post("/complaints/{id}/verify")
async def verify_complaint(
    id: int,
    req: AdminVerifyRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Human verification milestone: Verify AI categorization and severity.
    Optionally override AI predictions with documented justification.
    """
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    is_override = False
    override_notes = []

    if req.verified_category and req.verified_category != comp.category:
        override_notes.append(f"Category changed from '{comp.category}' to '{req.verified_category}'")
        comp.category = req.verified_category
        is_override = True

    if req.verified_severity and req.verified_severity != comp.severity:
        override_notes.append(f"Severity changed from '{comp.severity}' to '{req.verified_severity}'")
        comp.severity = req.verified_severity
        is_override = True

    if is_override:
        comp.admin_override = True
        comp.admin_override_reason = req.override_reason or "; ".join(override_notes)

        # Recalculate priority score with new human-adjusted severity/category
        from ai.priority_scorer import calculate_priority_score
        updated_p = calculate_priority_score(
            severity=comp.severity,
            category=comp.category,
            urgency_score=comp.ai_urgency_score,
            upvotes=comp.upvotes_count
        )
        comp.ai_priority_score = updated_p["priority_score"]
        comp.ai_priority_level = updated_p["priority_level"]

    if req.assigned_department:
        comp.assigned_department = req.assigned_department

    comp.status = "Verified"
    comp.verified_by = admin.full_name
    comp.verified_at = datetime.utcnow()

    # Timeline entry
    timeline_desc = (
        f"Verified by {admin.full_name} ({admin.role}). "
        + (f"Manual Override: {comp.admin_override_reason}." if is_override else "AI predictions confirmed.")
    )
    t = ComplaintTimeline(
        complaint_id=comp.id,
        status="Verified",
        title="Administrative Verification Completed",
        description=timeline_desc,
        performed_by=admin.full_name,
        created_at=datetime.utcnow()
    )
    db.add(t)

    # Audit log
    audit = AuditLog(
        action="VERIFY_COMPLAINT",
        entity_type="complaint",
        entity_id=str(comp.id),
        performed_by_id=admin.id,
        performed_by_email=admin.email,
        details=timeline_desc
    )
    db.add(audit)
    db.commit()

    await ws_manager.broadcast_event("STATUS_CHANGED", {
        "complaint_id": comp.id,
        "new_status": "Verified",
        "verified_by": admin.full_name
    })

    return {
        "success": True,
        "message": "Complaint verified successfully",
        "category": comp.category,
        "severity": comp.severity,
        "admin_override": comp.admin_override,
        "priority_score": comp.ai_priority_score
    }

@router.post("/complaints/{id}/assign")
async def assign_complaint(
    id: int,
    req: AdminAssignRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Assign complaint to a specific department and field officer with target SLA."""
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    comp.assigned_department = req.assigned_department
    if req.assigned_officer:
        comp.assigned_officer = req.assigned_officer
    comp.status = "Assigned"
    comp.sla_deadline = datetime.utcnow() + timedelta(hours=req.sla_hours or 48)

    t = ComplaintTimeline(
        complaint_id=comp.id,
        status="Assigned",
        title="Departmental Assignment",
        description=f"Formally assigned to {req.assigned_department} (Officer: {comp.assigned_officer or 'Field Supervisor'}). Resolution SLA: {req.sla_hours or 48} hours.",
        performed_by=admin.full_name,
        created_at=datetime.utcnow()
    )
    db.add(t)

    audit = AuditLog(
        action="ASSIGN_COMPLAINT",
        entity_type="complaint",
        entity_id=str(comp.id),
        performed_by_id=admin.id,
        performed_by_email=admin.email,
        details=f"Assigned to {req.assigned_department}"
    )
    db.add(audit)
    db.commit()

    await ws_manager.broadcast_event("STATUS_CHANGED", {
        "complaint_id": comp.id,
        "new_status": "Assigned",
        "assigned_department": comp.assigned_department
    })

    return {"success": True, "message": "Department successfully assigned", "sla_deadline": comp.sla_deadline}

@router.post("/complaints/{id}/status")
async def update_complaint_status(
    id: int,
    req: AdminStatusUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update workflow status (e.g. In_Progress, Resolved, Rejected).
    If Resolved, attaches resolution evidence notes and before/after photos.
    """
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")

    comp.status = req.status
    now = datetime.utcnow()

    if req.status == "Resolved":
        comp.resolved_at = now
        comp.resolution_notes = req.notes or "Civic repair work completed and inspected by municipal engineers."
        if req.resolution_image_urls:
            comp.resolution_image_urls = json.dumps(req.resolution_image_urls)

    t = ComplaintTimeline(
        complaint_id=comp.id,
        status=req.status,
        title=f"Status Updated to {req.status.replace('_', ' ')}",
        description=req.notes or f"Complaint status updated by {admin.full_name}.",
        performed_by=admin.full_name,
        created_at=now
    )
    db.add(t)

    audit = AuditLog(
        action=f"UPDATE_STATUS_{req.status}",
        entity_type="complaint",
        entity_id=str(comp.id),
        performed_by_id=admin.id,
        performed_by_email=admin.email,
        details=req.notes
    )
    db.add(audit)
    db.commit()

    await ws_manager.broadcast_event("STATUS_CHANGED", {
        "complaint_id": comp.id,
        "new_status": comp.status,
        "resolved_at": comp.resolved_at.isoformat() if comp.resolved_at else None
    })

    return {"success": True, "status": comp.status, "message": "Status updated successfully"}

@router.post("/complaints/merge-duplicates")
async def merge_duplicate_complaints(
    req: AdminMergeDuplicateRequest,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Merge duplicate complaint into primary complaint.
    Aggregates citizen upvotes, preserves record linking, and updates timeline.
    """
    primary = db.query(Complaint).filter(Complaint.id == req.primary_complaint_id).first()
    duplicate = db.query(Complaint).filter(Complaint.id == req.duplicate_complaint_id).first()

    if not primary or not duplicate:
        raise HTTPException(status_code=404, detail="Primary or duplicate complaint not found")

    # Transfer duplicate upvotes to primary
    transferred_votes = duplicate.upvotes_count
    primary.upvotes_count += max(1, transferred_votes)
    duplicate.status = "Duplicate_Merged"

    # Recalculate primary priority score
    from ai.priority_scorer import calculate_priority_score
    updated_p = calculate_priority_score(
        severity=primary.severity,
        category=primary.category,
        urgency_score=primary.ai_urgency_score,
        upvotes=primary.upvotes_count
    )
    primary.ai_priority_score = updated_p["priority_score"]
    primary.ai_priority_level = updated_p["priority_level"]

    # Record cluster
    cluster = DuplicateCluster(
        primary_complaint_id=primary.id,
        duplicate_complaint_id=duplicate.id,
        similarity_score=0.92,
        merged_at=datetime.utcnow()
    )
    db.add(cluster)

    t1 = ComplaintTimeline(
        complaint_id=primary.id,
        status="Duplicate_Merged",
        title="Duplicate Reports Merged",
        description=f"Linked duplicate complaint #{duplicate.tracking_id} reported by citizens in same area (+{transferred_votes} endorsements).",
        performed_by=admin.full_name,
        created_at=datetime.utcnow()
    )
    t2 = ComplaintTimeline(
        complaint_id=duplicate.id,
        status="Duplicate_Merged",
        title="Complaint Merged into Primary",
        description=f"Merged with master complaint #{primary.tracking_id} to unify municipal field response.",
        performed_by=admin.full_name,
        created_at=datetime.utcnow()
    )
    db.add_all([t1, t2])

    audit = AuditLog(
        action="MERGE_DUPLICATES",
        entity_type="complaint",
        entity_id=str(primary.id),
        performed_by_id=admin.id,
        performed_by_email=admin.email,
        details=f"Merged complaint #{duplicate.id} into #{primary.id}. Reason: {req.merge_reason}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully merged complaint #{duplicate.tracking_id} into primary #{primary.tracking_id}",
        "primary_upvotes": primary.upvotes_count,
        "new_priority_score": primary.ai_priority_score
    }

@router.get("/ai-models/metrics")
def get_ai_metrics(admin: User = Depends(get_current_admin)):
    """Fetch live AI model evaluation metrics and confusion matrices."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    metrics_path = os.path.join(base_dir, "ai", "models", "evaluation_metrics.json")
    cm_path = os.path.join(base_dir, "ai", "models", "confusion_matrices.json")

    if not os.path.exists(metrics_path) or not os.path.exists(cm_path):
        raise HTTPException(status_code=404, detail="Model evaluation metrics not found. Train models first.")

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    with open(cm_path, "r", encoding="utf-8") as f:
        cms = json.load(f)

    return {
        "metrics": metrics,
        "confusion_matrices": cms
    }

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Retrieve immutable administrative audit log."""
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "performed_by_email": l.performed_by_email,
            "details": l.details,
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]

@router.get("/export")
def export_complaints_csv(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Export all complaints as formatted CSV for government transparency reporting."""
    complaints = db.query(Complaint).order_by(desc(Complaint.created_at)).all()
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Tracking ID", "Title", "Category", "Severity", "Status",
        "Division", "District", "Upazila", "Area", "Priority Score",
        "Priority Level", "Department", "Upvotes", "Created At", "Resolved At"
    ])

    for c in complaints:
        writer.writerow([
            c.tracking_id, c.title, c.category, c.severity, c.status,
            c.division, c.district, c.upazila, c.area_name or "",
            c.ai_priority_score, c.ai_priority_level,
            c.assigned_department or "", c.upvotes_count,
            c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            c.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if c.resolved_at else ""
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=civicai_bangladesh_complaints.csv"}
    )
