from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings

# Adjust engine parameters based on database dialect
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL / Supabase
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency injection helper to yield database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Auto-creates all application tables on startup and safely runs column migrations."""
    import backend.app.models  # Ensure models are imported so Base registers them
    Base.metadata.create_all(bind=engine)

    # Safe auto-migration for newly added columns in SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                # Check attendance table columns
                res = conn.execute(text("PRAGMA table_info(attendance)")).fetchall()
                cols = [r[1] for r in res]
                if "face_visibility_score" not in cols:
                    conn.execute(text("ALTER TABLE attendance ADD COLUMN face_visibility_score FLOAT DEFAULT 100.0"))
                if "occlusion_count" not in cols:
                    conn.execute(text("ALTER TABLE attendance ADD COLUMN occlusion_count INTEGER DEFAULT 0"))

                # Check attendance_events table columns
                res_ev = conn.execute(text("PRAGMA table_info(attendance_events)")).fetchall()
                ev_cols = [r[1] for r in res_ev]
                if "is_occluded" not in ev_cols:
                    conn.execute(text("ALTER TABLE attendance_events ADD COLUMN is_occluded BOOLEAN DEFAULT 0"))
                if "occlusion_type" not in ev_cols:
                    conn.execute(text("ALTER TABLE attendance_events ADD COLUMN occlusion_type VARCHAR(50) DEFAULT 'unobstructed'"))
                if "visibility_score" not in ev_cols:
                    conn.execute(text("ALTER TABLE attendance_events ADD COLUMN visibility_score FLOAT DEFAULT 1.0"))
                conn.commit()
        except Exception as e:
            print(f"[Database] Migration note: {e}")
