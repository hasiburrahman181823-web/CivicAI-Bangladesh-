"""
CivicAI Bangladesh - Database Connection & Session Management
Supports SQLite and Neon PostgreSQL / PostGIS through SQLAlchemy 2.0.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database/civicai.db")

# Normalize SQLAlchemy PostgreSQL URL prefix (handle postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif "neon.tech" in DATABASE_URL or "sslmode=require" in DATABASE_URL:
    # Ensure SSL is active for cloud PostgreSQL (Neon / Supabase)
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
