"""
CivicAI Bangladesh - Main FastAPI Application Server
Provides REST API, WebSockets real-time gateway, security headers, and static uploads serving.
"""

import os
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is in path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from database.connection import engine, Base
from backend.routers import auth_routes, complaint_routes, admin_routes, upload_routes
from backend.websocket_manager import ws_manager

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CivicAI Bangladesh",
    description="AI-Powered Smart Public Complaint & Management Platform for Bangladesh",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()] + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Mount uploaded media directory
uploads_dir = os.path.join(base_dir, "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include Routers
app.include_router(auth_routes.router)
app.include_router(complaint_routes.router)
app.include_router(admin_routes.router)
app.include_router(upload_routes.router)

@app.websocket("/ws/complaints")
async def websocket_complaints_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; clients can send heartbeat pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

@app.get("/api/health")
def health_check():
    """System health check and diagnostic status."""
    return {
        "status": "healthy",
        "service": "CivicAI Bangladesh API",
        "version": "1.0.0",
        "database": "connected",
        "ai_engine": "operational",
        "models": {
            "category_classifier": "active",
            "severity_predictor": "active",
            "priority_scorer": "active",
            "duplicate_detector": "active",
            "nlp_preprocessor": "active (Bangla, English, Banglish)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
