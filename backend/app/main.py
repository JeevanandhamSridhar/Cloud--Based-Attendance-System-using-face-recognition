from contextlib import asynccontextmanager
import json
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.api import analytics, attendance, auth, sessions, students
from backend.app.config import settings
from backend.app.database import SessionLocal, init_db
from backend.app.models import FaceEmbedding, Student, Subject, User
from backend.app.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes tables and seeds default faculty account + synchronizes Phase 1 embeddings."""
    init_db()
    db = SessionLocal()
    try:
        # 1. Create Default Faculty User if not present
        default_email = "faculty@college.edu"
        user = db.query(User).filter(User.email == default_email).first()
        if not user:
            user = User(
                email=default_email,
                password_hash=get_password_hash("Password123!"),
                full_name="Dr. Alexander Reed (Faculty Admin)",
                role="faculty",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[Startup] Created default faculty account: {default_email} / Password123!")

        # 2. Create Default Subject if none exist
        if db.query(Subject).count() == 0:
            subj = Subject(
                code="CS301",
                name="Data Structures & Algorithms",
                department="Computer Science",
                faculty_id=user.id,
            )
            db.add(subj)
            db.commit()
            print("[Startup] Seeded default course: CS301 - Data Structures & Algorithms")

        # User manages student data from scratch - zero auto-seeding

    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend AI & REST API for Smart Attendance with Facial Recognition, Liveness, and Continuous Presence Scoring.",
    lifespan=lifespan,
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(students.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(attendance.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "author": "Smart Attendance Research Group",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
