import io
import json
import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import func, select

from ..db import get_db
from ..models import Audit, Complaint, ComplaintIntake, TicketEvent, TicketEvidence, TicketMessage
from ..privacy import redact_contact
from ..schemas import ContactAccessInput, FollowupInput
from ..security import get_session, throttle
from ..services.intake import contact_reviewers, masked_contact, open_intake


router = APIRouter(prefix="/api/tickets")
MAX_IMAGE_SIZE = 2 * 1024 * 1024
MAX_IMAGES = 5


def ticket_access(complaint_id, request, db, *, lock=False):
    user, _ = get_session(request, db)
    query = select(Complaint).where(Complaint.id == str(complaint_id))
    if user.role != "admin":
        query = query.where(Complaint.owner_id == user.id)
    item = db.scalar(query.with_for_update() if lock else query)
    if item is None:
        raise HTTPException(404, "Ticket not found")
    return item, user


def utc(value):
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)


def estimate_resolution(db, item):
    if item.status == "Resolved":
        return None
    resolved = (
        select(TicketEvent.complaint_id, func.max(TicketEvent.created_at).label("at"))
        .where(TicketEvent.status == "Resolved")
        .group_by(TicketEvent.complaint_id).subquery()
    )
    recent = (
        select(Complaint.created_at, resolved.c.at)
        .join(resolved, resolved.c.complaint_id == Complaint.id)
        .where(Complaint.category == item.category, Complaint.status == "Resolved",
               resolved.c.at >= datetime.now(timezone.utc) - timedelta(days=365))
        .order_by(resolved.c.at.desc()).limit(200)
    )
    hours = sorted((utc(end) - utc(start)).total_seconds() / 3600
                   for start, end in db.execute(recent) if utc(end) > utc(start))
    if len(hours) < 20:
        return None
    lower, middle, upper = (hours[math.floor((len(hours) - 1) * p)] for p in (.2, .5, .8))
    return {
        "median_hours": max(1, round(middle)), "typical_min_hours": max(1, round(lower)),
        "typical_max_hours": max(1, round(upper)), "sample_size": len(hours),
        "estimated_at": utc(item.created_at) + timedelta(hours=middle),
    }


def message_json(message):
    return {"id": message.id, "role": message.author_role, "body": message.body,
            "created_at": utc(message.created_at)}


@router.get("/{complaint_id}")
def ticket(complaint_id: uuid.UUID, request: Request, db=Depends(get_db)):
    item, user = ticket_access(complaint_id, request, db)
    throttle(request, "ticket-read", 90, identity=str(user.id))
    messages = db.scalars(select(TicketMessage).where(TicketMessage.complaint_id == item.id)
                          .order_by(TicketMessage.id.desc()).limit(100)).all()
    events = db.scalars(select(TicketEvent).where(TicketEvent.complaint_id == item.id)
                        .order_by(TicketEvent.id.desc()).limit(100)).all()
    evidence = db.execute(select(TicketEvidence.id, TicketEvidence.size, TicketEvidence.created_at)
                          .where(TicketEvidence.complaint_id == item.id)
                          .order_by(TicketEvidence.created_at)).all()
    result = {
        "id": item.id, "title": item.title, "text": item.text, "area": item.area,
        "category": item.category, "priority": item.priority, "status": item.status,
        "created_at": utc(item.created_at), "estimate": estimate_resolution(db, item),
        "messages": [message_json(message) for message in reversed(messages)],
        "history": [{"id": event.id, "status": event.status, "created_at": utc(event.created_at)}
                    for event in reversed(events)],
        "evidence": [{"id": id, "size": size, "created_at": utc(at)} for id, size, at in evidence],
    }
    if not events or events[-1].created_at > item.created_at:
        result["history"].insert(0, {"id": 0, "status": "Submitted", "created_at": utc(item.created_at)})
    if user.role == "admin":
        result.update({
            "intake": masked_contact(db.get(ComplaintIntake, item.id)),
            "can_reveal": user.email in contact_reviewers,
            "assessment": (item.analysis or {}).get("assessment"),
            "can_reply": item.owner_id is not None,
        })
    return result


@router.post("/{complaint_id}/messages", status_code=201)
def send_message(complaint_id: uuid.UUID, payload: FollowupInput, request: Request, db=Depends(get_db)):
    item, user = ticket_access(complaint_id, request, db)
    if item.owner_id is None:
        raise HTTPException(409, "This ticket was submitted without a citizen account")
    throttle(request, "ticket-message", 8, identity=str(user.id))
    message = TicketMessage(complaint_id=item.id, author_id=user.id, author_role=user.role,
                            body=redact_contact(payload.body))
    db.add(message)
    if user.role == "admin":
        db.add(Audit(actor_id=user.id, complaint_id=item.id, action='{"event":"ticket_reply"}'))
    db.commit()
    return message_json(message)


def sanitize_image(blob):
    try:
        with Image.open(io.BytesIO(blob), formats=("JPEG", "PNG", "WEBP")) as original:
            if original.width * original.height > 12_000_000 or getattr(original, "n_frames", 1) != 1:
                raise ValueError("Unsupported image")
            original.thumbnail((1600, 1600))
            image = ImageOps.exif_transpose(original).convert("RGB")
            output = io.BytesIO()
            clean = Image.new("RGB", image.size)
            clean.paste(image)
            clean.save(output, format="JPEG", quality=85)
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
        raise HTTPException(422, "Upload a valid JPEG, PNG or WebP image under 12 megapixels") from error
    return output.getvalue()


@router.post("/{complaint_id}/evidence", status_code=201)
def upload_evidence(complaint_id: uuid.UUID, request: Request, file: UploadFile = File(), db=Depends(get_db)):
    item, user = ticket_access(complaint_id, request, db, lock=True)
    if item.owner_id != user.id or user.role == "admin":
        raise HTTPException(403, "Only the ticket owner can submit evidence")
    throttle(request, "ticket-upload", 5, identity=str(user.id))
    count = db.scalar(select(func.count()).select_from(TicketEvidence)
                      .where(TicketEvidence.complaint_id == item.id))
    if count >= MAX_IMAGES:
        raise HTTPException(409, "This ticket already has five evidence images")
    blob = file.file.read(MAX_IMAGE_SIZE + 1)
    if len(blob) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Evidence images must be at most 2 MB")
    image = sanitize_image(blob)
    if len(image) > MAX_IMAGE_SIZE:
        raise HTTPException(413, "Evidence image exceeds the storage limit")
    proof = TicketEvidence(id=str(uuid.uuid4()), complaint_id=item.id, image=image, size=len(image))
    db.add(proof)
    db.commit()
    return {"id": proof.id, "size": proof.size, "created_at": utc(proof.created_at)}


@router.get("/{complaint_id}/evidence/{evidence_id}")
def download_evidence(complaint_id: uuid.UUID, evidence_id: uuid.UUID, request: Request, db=Depends(get_db)):
    item, user = ticket_access(complaint_id, request, db)
    throttle(request, "ticket-download", 30, identity=str(user.id))
    proof = db.scalar(select(TicketEvidence).where(TicketEvidence.id == str(evidence_id),
                                                   TicketEvidence.complaint_id == item.id))
    if proof is None:
        raise HTTPException(404, "Evidence not found")
    if user.role == "admin":
        db.add(Audit(actor_id=user.id, complaint_id=item.id, action='{"event":"evidence_download"}'))
        db.commit()
    return Response(proof.image, media_type="image/jpeg", headers={
        "Content-Disposition": f'attachment; filename="evidence-{proof.id}.jpg"',
    })


@router.post("/{complaint_id}/contact")
def reveal_contact(complaint_id: uuid.UUID, payload: ContactAccessInput, request: Request, db=Depends(get_db)):
    user, _ = get_session(request, db)
    if user.role != "admin" or user.email not in contact_reviewers:
        raise HTTPException(403, "Contact review permission required")
    throttle(request, "contact-reveal", 10, identity=str(user.id))
    intake = db.get(ComplaintIntake, str(complaint_id))
    if intake is None:
        raise HTTPException(404, "No contact record for this ticket")
    value = open_intake(intake)
    action = json.dumps({"event": "contact_access", "reason": redact_contact(payload.reason)})
    db.add(Audit(actor_id=user.id, complaint_id=intake.complaint_id, action=action))
    db.commit()
    return value
