import csv
import hashlib
import io
import json
import re
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete, func, or_, literal, union_all, text
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import ALLOWED_HOSTS, CORS_ORIGINS, PRODUCTION
from .db import Base, engine, get_db
from .models import AdminExportAudit, Audit, CitizenContact, Complaint, ComplaintIntake, LoginSession, TicketEvent, TicketMessage, User
from .schemas import Credentials, Registration, ComplaintSuggestion, ComplaintSubmission, ReviewInput, TrackingInput
from .services.analysis import analyze, candidate_context, duplicate_candidates
from .ml.embeddings import load_encoder
from .ml.predict import ARTIFACTS, benchmark_forecast, load_text
from .ml.intake import assess, load_intake_model
from .routers.media import router as media_router
from .routers.recovery import router as recovery_router
from .routers.tickets import router as ticket_router
from .services.intake import masked_contact, seal_intake, vault
from .services.evidence import evidence_json, evidence_record, prepare_evidence
from .privacy import redact_input, redact_contact
from .security import COOKIE, RequestProtection, configure_limit_store, get_session, guarded_password_operation, hasher, issue_session, limits, session_digest, throttle
from .ml.integrity import verify_artifacts

encoder = None
text_model = None
dummy_hash = hasher.hash(secrets.token_urlsafe(32))

@asynccontextmanager
async def lifespan(app):
    global encoder, text_model
    configure_limit_store()
    verify_artifacts(ARTIFACTS)
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(81726023)"))
        Base.metadata.create_all(connection)
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_complaints_owner_created ON complaints (owner_id, created_at DESC)"
        ))
    encoder = load_encoder()
    text_model = load_text()
    load_intake_model()
    yield

app = FastAPI(title="CivicAI Bangladesh", lifespan=lifespan, docs_url=None,
              redoc_url=None, openapi_url=None if PRODUCTION else "/openapi.json")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"],
                   allow_credentials=True)
app.add_middleware(RequestProtection)
app.include_router(media_router)
app.include_router(recovery_router)
app.include_router(ticket_router)

@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    # Default Pydantic details may echo passwords, tokens or private complaint input.
    details = [{"field":".".join(map(str,item["loc"])), "type":item["type"]}
               for item in error.errors()]
    return JSONResponse(status_code=422,content={"detail":"Check the submitted fields","fields":details})

@app.exception_handler(OperationalError)
async def database_unavailable(request, error):
    return JSONResponse(status_code=503, content={"detail": "Database temporarily unavailable"})


def current_user(request: Request, db=Depends(get_db)):
    return get_session(request, db)[0]

def admin(request: Request, db=Depends(get_db)):
    user, _ = get_session(request, db)
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return user

def serialize(item):
    return {key: getattr(item, key) for key in ['id', 'title', 'text', 'area', 'language', 'latitude', 'longitude', 'occurred_at', 'created_at', 'category', 'priority', 'score', 'status', 'analysis', 'duplicate_of']}

@app.get('/api/health')
def health():
    return {'status': 'ok', 'classification': 'trained' if text_model else 'rules', 'embeddings': encoder is not None, 'calibrated_model': text_model is not None, 'voice': (ARTIFACTS / 'whisper/model.bin').is_file(), 'image': (ARTIFACTS / 'road/road.onnx').is_file(), 'closure_benchmark': (ARTIFACTS / 'forecast.joblib').is_file()}

@app.get('/api/public/summary')
def public_summary(request: Request, db=Depends(get_db)):
    throttle(request, 'public-summary', 60)
    status_counts = {'Submitted': 0, 'Under review': 0, 'In progress': 0, 'Resolved': 0}
    categories = {}
    total = 0
    for status, category, count in db.execute(
        select(Complaint.status, Complaint.category, func.count()).group_by(Complaint.status, Complaint.category)
    ):
        total += count
        if status in status_counts:
            status_counts[status] += count
        categories[category] = categories.get(category, 0) + count
    # Publish only overall totals and sufficiently large categories.
    return {
        'total': total,
        'resolved': status_counts['Resolved'],
        'in_progress': status_counts['In progress'],
        'awaiting_action': status_counts['Submitted'] + status_counts['Under review'],
        'categories': [
            {'name': name, 'count': count}
            for name, count in sorted(categories.items(), key=lambda item: (-item[1], item[0]))
            if count >= 5
        ],
    }

@app.get("/api/research/closure-benchmark")
def closure_benchmark(category: str, occurred_at: datetime):
    if occurred_at.tzinfo is None:
        raise HTTPException(422, "Provide timezone information")
    result = benchmark_forecast(category, occurred_at.astimezone(timezone.utc))
    if not result:
        raise HTTPException(404, "Benchmark unavailable for this category")
    return result

@app.post("/api/auth/register")
def register(data: Registration, request: Request, db=Depends(get_db)):
    throttle(request, "register", 3)
    password_hash = guarded_password_operation(hasher.hash, data.password)
    user = User(email=data.email, password_hash=password_hash)
    db.add(user)
    try:
        db.flush()
        db.add(CitizenContact(user_id=user.id, name=data.name, sealed_mobile=vault.encrypt(data.mobile.encode()),
                              mobile_last4=data.mobile[-4:]))
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"message": "You can sign in with your account details."}

@app.post("/api/auth/login")
def login(data: Credentials, request: Request, response: Response, db=Depends(get_db)):
    return authenticate(data, request, response, db, role="citizen")


@app.post("/api/auth/admin/login")
def admin_login(data: Credentials, request: Request, response: Response, db=Depends(get_db)):
    return authenticate(data, request, response, db, role="admin")


def authenticate(data, request, response, db, *, role):
    throttle(request, "login", 5)
    throttle(request, "login-account", 8, identity=data.email)
    user = db.scalar(select(User).where(User.email == data.email, User.role == role))
    verified_hash = user.password_hash if user else dummy_hash
    try:
        guarded_password_operation(hasher.verify, verified_hash, data.password)
    except VerificationError:
        raise HTTPException(401, "Invalid email or password")
    if not user:
        raise HTTPException(401, "Invalid email or password")
    updated_hash = guarded_password_operation(hasher.hash, data.password) if verified_hash.startswith("$argon2") else None
    user = db.get(User, user.id, with_for_update=True, populate_existing=True)
    if not user or user.role != role or user.password_hash != verified_hash:
        raise HTTPException(401, "Invalid email or password")
    if updated_hash:
        user.password_hash = updated_hash
    issue_session(db, user, response, prior_token=request.cookies.get(COOKIE))
    return account_summary(user, db)

@app.get("/api/auth/me")
def me(user=Depends(current_user), db=Depends(get_db)):
    return account_summary(user, db)


def account_summary(user, db):
    result = {"role": user.role, "email": user.email}
    contact = db.get(CitizenContact, user.id)
    if contact is not None:
        result.update(name=contact.name, mobile="•••• " + contact.mobile_last4)
    return result


@app.get("/admin", include_in_schema=False)
def admin_entry():
    return RedirectResponse("/#admin", status_code=307)

@app.get("/api/auth/me/complaints")
def my_complaints(user=Depends(current_user), db=Depends(get_db)):
    query = (
        select(Complaint.id, Complaint.title, Complaint.area, Complaint.status, Complaint.created_at)
        .where(Complaint.owner_id == user.id)
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
        .limit(100)
    )
    reports = []
    for row in db.execute(query).mappings():
        created_at = row["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        reports.append({**row, "created_at": created_at.astimezone(timezone.utc).isoformat()})
    return reports


@app.get("/api/auth/me/updates")
def my_updates(request: Request, user=Depends(current_user), db=Depends(get_db)):
    throttle(request, "my-updates", 60, identity=str(user.id))
    status_updates = (
        select(TicketEvent.id.label("id"), Complaint.id.label("ticket_id"), Complaint.title.label("title"),
               TicketEvent.created_at.label("created_at"), TicketEvent.status.label("kind"))
        .join(Complaint, Complaint.id == TicketEvent.complaint_id)
        .where(Complaint.owner_id == user.id,
               or_(TicketEvent.status != "Submitted", TicketEvent.created_at > Complaint.created_at))
    )
    replies = (
        select(TicketMessage.id, Complaint.id, Complaint.title, TicketMessage.created_at, literal("reply"))
        .join(Complaint, Complaint.id == TicketMessage.complaint_id)
        .where(Complaint.owner_id == user.id, TicketMessage.author_role == "admin")
    )
    stream = union_all(status_updates, replies).subquery()
    return [
        {**row, "created_at": (row["created_at"].replace(tzinfo=timezone.utc)
                              if row["created_at"].tzinfo is None else row["created_at"])}
        for row in db.execute(select(stream).order_by(stream.c.created_at.desc(), stream.c.kind, stream.c.id.desc())
                              .limit(20)).mappings()
    ]

@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db=Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(LoginSession).where(LoginSession.digest == session_digest(token)))
        db.commit()
    response.delete_cookie(COOKIE,path="/",secure=PRODUCTION,httponly=True,samesite="strict")
    return {"message":"Signed out"}

@app.post('/api/analyze')
def analysis(data: ComplaintSuggestion, request: Request):
    throttle(request, 'analyze', 10)
    return analyze(redact_contact(data.text), text_model, data.language)

@app.post('/api/complaints')
def create(data: ComplaintSubmission, request: Request, db=Depends(get_db)):
    return save_complaint(data, request, db)


@app.post('/api/complaints/with-evidence')
def create_with_evidence(request: Request, complaint: str = Form(max_length=12000),
                         file: UploadFile = File(), db=Depends(get_db)):
    try:
        data = ComplaintSubmission.model_validate_json(complaint)
    except ValidationError as error:
        raise HTTPException(422, "Check the submitted fields") from error
    return save_complaint(data, request, db, file)


def save_complaint(data: ComplaintSubmission, request: Request, db, file: UploadFile | None = None):
    throttle(request, 'submit', 5)
    user, _ = get_session(request, db, required=False)
    if not user and not data.mobile:
        raise HTTPException(422, "A Bangladesh mobile number is required for guest complaints")
    if not user:
        throttle(request, "submit-guest-mobile", 3, identity=data.mobile)
    media = prepare_evidence(file) if file is not None else None
    data = redact_input(data)
    tracking_key = secrets.token_urlsafe(24)
    result = analyze(data.text, text_model, data.language, data.occurred_at)
    result["assessment"] = assess(data.title, data.text, result["category"], result["priority"])
    item = Complaint(id=str(uuid.uuid4()), tracking_hash=hashlib.sha256(tracking_key.encode()).hexdigest(),
                     owner_id=user.id if user else None, **data.model_dump(exclude={"mobile"}),
                     category=result["category"], priority=result["priority"], score=result["score"], analysis=result)
    db.add(item)
    db.flush()
    db.add(seal_intake(item, data.mobile, request))
    db.add(TicketEvent(complaint_id=item.id, status=item.status, created_at=item.created_at))
    evidence = evidence_record(item.id, *media) if media else None
    if evidence is not None:
        db.add(evidence)
    db.commit()
    response = serialize(item)
    response["analysis"] = {key: value for key, value in result.items() if key != "assessment"}
    if evidence is not None:
        response["evidence"] = evidence_json(evidence)
    return {**response, "tracking_key": tracking_key}

@app.post('/api/track/{complaint_id}')
def track(complaint_id: uuid.UUID, payload: TrackingInput, request: Request, db=Depends(get_db)):
    throttle(request, 'track', 15)
    item = db.get(Complaint, str(complaint_id))
    key = hashlib.sha256(payload.tracking_key.encode()).hexdigest()
    good_key = secrets.compare_digest(item.tracking_hash if item else "0"*64, key)
    if not item or not good_key:
        raise HTTPException(404, "Complaint or tracking key not found")
    return {key: getattr(item,key) for key in ("id","title","category","priority","status","created_at")}

def admin_filters(status: str = Query(default="", max_length=24),
                  category: str = Query(default="", max_length=32),
                  area: str = Query(default="", max_length=120),
                  after: datetime | None = None, before: datetime | None = None,
                  search: str = Query(default="", max_length=120), review_only: bool = False):
    if any(value is not None and value.tzinfo is None for value in (after, before)):
        raise HTTPException(422, "Filters must include timezone information")
    if after and before and after > before:
        raise HTTPException(422, "The start date must precede the end date")
    query = select(Complaint, ComplaintIntake).outerjoin(ComplaintIntake)
    if status:
        query = query.where(Complaint.status == status)
    if review_only:
        query = query.where(Complaint.status != "Resolved",
                            Complaint.analysis["requires_review"].as_boolean().is_not(False))
    if category:
        query = query.where(Complaint.category == category)
    if area:
        query = query.where(Complaint.area.icontains(area, autoescape=True))
    if after:
        query = query.where(Complaint.occurred_at >= after.astimezone(timezone.utc))
    if before:
        query = query.where(Complaint.occurred_at <= before.astimezone(timezone.utc))
    if search:
        query = query.where(or_(*(field.icontains(search, autoescape=True)
                                  for field in (Complaint.title, Complaint.text, Complaint.area, Complaint.id))))
    return query.order_by(Complaint.created_at.desc(), Complaint.id.desc())


@app.get('/api/admin/complaints')
def all_complaints(query=Depends(admin_filters), offset: int = Query(default=0, ge=0),
                   limit: int = Query(default=500, ge=1, le=500), user=Depends(admin), db=Depends(get_db)):
    return [{**serialize(item), "intake": masked_contact(intake)}
            for item, intake in db.execute(query.offset(offset).limit(limit))]


def csv_cell(value):
    text = str(value if value is not None else "")
    return "'" + text if re.match(r"^[\s\u200b-\u200f]*[=+@\-]|^[\t\r\n]", text) else text


@app.get('/api/admin/complaints/export')
def export_complaints(request: Request, offset: int = Query(default=0, ge=0),
                      query=Depends(admin_filters), user=Depends(admin), db=Depends(get_db)):
    throttle(request, "admin-export", 6, identity=str(user.id))
    reports = db.execute(query.offset(offset).limit(5001)).all()
    if len(reports) > 5000:
        raise HTTPException(422, "Filter the report to 5000 complaints or fewer")
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(("Tracking ID", "Title", "Area", "Incident time", "Submission time", "Category",
                     "Priority", "Status", "Language", "Masked mobile", "Mobile verified", "Review flags"))
    for item, intake in reports:
        contact = masked_contact(intake) or {}
        flags = (item.analysis.get("assessment") or {}).get("flags", [])
        writer.writerow(map(csv_cell, (item.id, item.title, item.area, item.occurred_at, item.created_at,
                                       item.category, item.priority, item.status, item.language,
                                       contact.get("mobile"), contact.get("verified"), ", ".join(flags))))
    db.add(AdminExportAudit(actor_id=user.id, count=len(reports)))
    db.commit()
    return Response("\ufeff" + output.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": 'attachment; filename="civicai-complaints.csv"',
    })

def recent_complaints():
    return select(Complaint).order_by(Complaint.created_at.desc(), Complaint.id.desc()).limit(500)

@app.patch('/api/admin/complaints/{complaint_id}')
def review(complaint_id: str, data: ReviewInput, user=Depends(admin), db=Depends(get_db)):
    item = db.get(Complaint, complaint_id, with_for_update=True)
    if not item:
        raise HTTPException(404, 'Complaint not found')
    if data.duplicate_of:
        target = db.get(Complaint, data.duplicate_of)
        if not target or target.id == item.id or target.duplicate_of:
            raise HTTPException(400, 'Select a separate original incident')
        if candidate_context(item, target) is None or target.status == 'Resolved':
            raise HTTPException(400, 'The selected incident has incompatible location, time or status')
        if db.scalar(select(Complaint).where(Complaint.duplicate_of == item.id)):
            raise HTTPException(400, 'Move existing linked reports before linking this incident')
    if item.status != data.status:
        db.add(TicketEvent(complaint_id=item.id, status=data.status))
    for key in ['status', 'priority', 'duplicate_of']:
        setattr(item, key, getattr(data, key))
    note = redact_contact(data.note)
    item.analysis = {**item.analysis, 'requires_review': False, 'review_note': note}
    db.add(Audit(actor_id=user.id, complaint_id=item.id, action=data.model_copy(update={'note':note}).model_dump_json()))
    db.commit()
    return {**serialize(item), "intake": masked_contact(db.get(ComplaintIntake, item.id))}

@app.get('/api/admin/duplicates/{complaint_id}')
def duplicates(complaint_id: str, request: Request, user=Depends(admin), db=Depends(get_db)):
    throttle(request,"admin-duplicates",60,identity=str(user.id))
    item = db.get(Complaint, complaint_id)
    if not item:
        raise HTTPException(404, 'Complaint not found')
    return duplicate_candidates(item, db.scalars(recent_complaints()).all(), encoder)

@app.get('/api/admin/audit')
def audit(user=Depends(admin), db=Depends(get_db)):
    events = [
        {"id": row.id, "complaint_id": row.complaint_id, "actor_id": row.actor_id,
         "action": row.action, "created_at": row.created_at}
        for row in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))
    ]
    events.extend({
        "id": f"export-{row.id}", "complaint_id": None, "actor_id": row.actor_id,
        "action": json.dumps({"event": "complaint_export", "count": row.count}), "created_at": row.created_at,
    } for row in db.scalars(select(AdminExportAudit).order_by(AdminExportAudit.id.desc()).limit(100)))
    return sorted(events, key=lambda event: event["created_at"], reverse=True)[:100]

# Mount only after API routes, so the bundled production frontend shares the origin.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
static_path = Path(__file__).resolve().parents[2] / 'dist'
if static_path.is_dir():
    app.mount('/', StaticFiles(directory=static_path, html=True), name='frontend')
