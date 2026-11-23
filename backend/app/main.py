import hashlib
import secrets
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from threading import BoundedSemaphore
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, OperationalError
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import ALLOWED_HOSTS, CORS_ORIGINS, PRODUCTION
from .db import Base, engine, get_db
from .models import AdminMFA, Audit, Complaint, LoginSession, User
from .schemas import Credentials, Login, ComplaintInput, ReviewInput, TrackingInput
from .services.analysis import analyze, candidate_context, duplicate_candidates
from .ml.embeddings import load_encoder
from .ml.predict import ARTIFACTS, benchmark_forecast, load_text
from .routers.media import router as media_router
from .mfa import verify_once
from .privacy import redact_input, redact_contact
from .security import COOKIE, RequestProtection, configure_limit_store, get_session, issue_session, limits, session_digest, throttle
from .ml.integrity import verify_artifacts

encoder = None
text_model = None
hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_urlsafe(32))
password_slots = BoundedSemaphore(2)

@asynccontextmanager
async def lifespan(app):
    global encoder, text_model
    configure_limit_store()
    verify_artifacts(ARTIFACTS)
    Base.metadata.create_all(engine)
    encoder = load_encoder()
    text_model = load_text()
    yield

app = FastAPI(title="CivicAI Bangladesh", lifespan=lifespan, docs_url=None,
              redoc_url=None, openapi_url=None if PRODUCTION else "/openapi.json")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS,
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"],
                   allow_credentials=True)
app.add_middleware(RequestProtection)
app.include_router(media_router)

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
    user, session = get_session(request, db)
    if user.role != "admin" or (PRODUCTION and not session.mfa_verified):
        raise HTTPException(403, "Administrator access requires MFA")
    return user

def serialize(item):
    return {key: getattr(item, key) for key in ['id', 'title', 'text', 'area', 'language', 'latitude', 'longitude', 'occurred_at', 'created_at', 'category', 'priority', 'score', 'status', 'analysis', 'duplicate_of']}

@app.get('/api/health')
def health():
    return {'status': 'ok', 'classification': 'trained' if text_model else 'rules', 'embeddings': encoder is not None, 'calibrated_model': text_model is not None, 'voice': (ARTIFACTS / 'whisper/model.bin').is_file(), 'image': (ARTIFACTS / 'road/road.onnx').is_file()}

@app.get("/api/research/closure-benchmark")
def closure_benchmark(category: str, occurred_at: datetime):
    if occurred_at.tzinfo is None:
        raise HTTPException(422, "Provide timezone information")
    result = benchmark_forecast(category, occurred_at.astimezone(timezone.utc))
    if not result:
        raise HTTPException(404, "Benchmark unavailable for this category")
    return result

def guarded_password_operation(function, *args):
    if not password_slots.acquire(blocking=False):
        raise HTTPException(429, "Authentication is busy. Please try again.")
    try:
        return function(*args)
    finally:
        password_slots.release()

@app.post("/api/auth/register")
def register(data: Credentials, request: Request, db=Depends(get_db)):
    throttle(request, "register", 3)
    password_hash = guarded_password_operation(hasher.hash, data.password)
    db.add(User(email=data.email, password_hash=password_hash))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
    return {"message": "You can sign in with your account details."}

@app.post("/api/auth/login")
def login(data: Login, request: Request, response: Response, db=Depends(get_db)):
    throttle(request, "login", 5)
    throttle(request, "login-account", 8, identity=data.email)
    user = db.scalar(select(User).where(User.email == data.email))
    try:
        guarded_password_operation(hasher.verify, user.password_hash if user else dummy_hash, data.password)
    except VerificationError:
        raise HTTPException(401, "Invalid email, password or authenticator code")
    if not user:
        raise HTTPException(401, "Invalid email, password or authenticator code")
    verified = False
    if user.role == "admin":
        enrollment = db.get(AdminMFA, user.id)
        if enrollment:
            verified = verify_once(db, enrollment, data.otp)
            if not verified:
                raise HTTPException(401, "Enter a current unused authenticator code")
        elif PRODUCTION:
            raise HTTPException(403, "Administrator enrollment is required")
    issue_session(db,user,response,verified,request.cookies.get(COOKIE))
    return {"role":user.role,"email":user.email}

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return {"role":user.role,"email":user.email}

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

@app.post("/api/auth/logout")
def logout(request: Request, response: Response, db=Depends(get_db)):
    token = request.cookies.get(COOKIE)
    if token:
        db.execute(delete(LoginSession).where(LoginSession.digest == session_digest(token)))
        db.commit()
    response.delete_cookie(COOKIE,path="/",secure=PRODUCTION,httponly=True,samesite="strict")
    return {"message":"Signed out"}

@app.post('/api/analyze')
def analysis(data: ComplaintInput, request: Request):
    throttle(request, 'analyze', 10)
    data = redact_input(data)
    return analyze(data.text, text_model, data.language, data.occurred_at)

@app.post('/api/complaints')
def create(data: ComplaintInput, request: Request, db=Depends(get_db)):
    throttle(request, 'submit', 5)
    data = redact_input(data)
    tracking_key = secrets.token_urlsafe(24)
    result = analyze(data.text, text_model, data.language, data.occurred_at)
    item = Complaint(id=str(uuid.uuid4()), tracking_hash=hashlib.sha256(tracking_key.encode()).hexdigest(), **data.model_dump(), category=result['category'], priority=result['priority'], score=result['score'], analysis=result)
    user, _ = get_session(request, db, required=False)
    if user:
        item.owner_id = user.id
    db.add(item)
    db.commit()
    return {**serialize(item), 'tracking_key': tracking_key}

@app.post('/api/track/{complaint_id}')
def track(complaint_id: uuid.UUID, payload: TrackingInput, request: Request, db=Depends(get_db)):
    throttle(request, 'track', 15)
    item = db.get(Complaint, str(complaint_id))
    key = hashlib.sha256(payload.tracking_key.encode()).hexdigest()
    good_key = secrets.compare_digest(item.tracking_hash if item else "0"*64, key)
    if not item or not good_key:
        raise HTTPException(404, "Complaint or tracking key not found")
    return {key: getattr(item,key) for key in ("id","title","category","priority","status","created_at")}

@app.get('/api/admin/complaints')
def all_complaints(user=Depends(admin), db=Depends(get_db)):
    return [serialize(item) for item in db.scalars(select(Complaint).order_by(Complaint.created_at.desc()).limit(500))]

@app.patch('/api/admin/complaints/{complaint_id}')
def review(complaint_id: str, data: ReviewInput, user=Depends(admin), db=Depends(get_db)):
    item = db.get(Complaint, complaint_id)
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
    for key in ['status', 'priority', 'duplicate_of']:
        setattr(item, key, getattr(data, key))
    note = redact_contact(data.note)
    item.analysis = {**item.analysis, 'requires_review': False, 'review_note': note}
    db.add(Audit(actor_id=user.id, complaint_id=item.id, action=data.model_copy(update={'note':note}).model_dump_json()))
    db.commit()
    return serialize(item)

@app.get('/api/admin/duplicates/{complaint_id}')
def duplicates(complaint_id: str, request: Request, user=Depends(admin), db=Depends(get_db)):
    throttle(request,"admin-duplicates",60,identity=str(user.id))
    item = db.get(Complaint, complaint_id)
    if not item:
        raise HTTPException(404, 'Complaint not found')
    return duplicate_candidates(item, db.scalars(select(Complaint).limit(500)).all(), encoder)

@app.get('/api/admin/audit')
def audit(user=Depends(admin), db=Depends(get_db)):
    return [{'id': x.id, 'complaint_id': x.complaint_id, 'action': x.action, 'created_at': x.created_at} for x in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))]

# Mount only after API routes, so the bundled production frontend shares the origin.
from pathlib import Path
from fastapi.staticfiles import StaticFiles
static_path = Path(__file__).resolve().parents[2] / 'dist'
if static_path.is_dir():
    app.mount('/', StaticFiles(directory=static_path, html=True), name='frontend')
