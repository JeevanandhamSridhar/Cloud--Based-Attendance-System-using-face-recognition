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
                full_name="Prof. Jeevanandham",
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

        # 3. Synchronize any existing Phase 1 embeddings from data/embeddings.json
        embeddings_file = os.path.join("data", "embeddings.json")
        if os.path.exists(embeddings_file):
            try:
                with open(embeddings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for sid, record in data.items():
                        student = db.query(Student).filter(Student.student_id == sid).first()
                        if not student:
                            student = Student(
                                student_id=sid,
                                name=record.get("name", "Student"),
                                department=record.get("department", "Computer Science"),
                                year=3,
                                section="A",
                            )
                            db.add(student)
                            db.commit()
                            db.refresh(student)

                        has_emb = (
                            db.query(FaceEmbedding)
                            .filter(FaceEmbedding.student_id == student.id)
                            .first()
                        )
                        if not has_emb and "embedding" in record:
                            face_rec = FaceEmbedding(
                                student_id=student.id,
                                embedding_json=json.dumps(record["embedding"]),
                                model_version=record.get("model", "ArcFace_buffalo_sc_512"),
                            )
                            db.add(face_rec)
                            db.commit()
                            print(f"[Startup] Synced Phase 1 face vector for {student.name} ({sid})")
            except Exception as e:
                print(f"[Startup] Error syncing Phase 1 embeddings: {e}")

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
        "author": "Jeevanandham S",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
