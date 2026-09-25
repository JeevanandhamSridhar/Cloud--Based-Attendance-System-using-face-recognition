import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import ClassSession, Subject, User
from backend.app.schemas import (
    SessionCreate,
    SessionResponse,
    SubjectCreate,
    SubjectResponse,
)
from backend.app.security import get_current_user, require_faculty_or_admin

router = APIRouter(prefix="/sessions", tags=["Class Sessions"])


# ------------------------------------------------------------------
# SUBJECT MANAGEMENT
# ------------------------------------------------------------------
@router.get("/subjects", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/subjects", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subj_in: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    existing = db.query(Subject).filter(Subject.code == subj_in.code).first()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Subject with code '{subj_in.code}' already exists."
        )

    subject = Subject(
        code=subj_in.code,
        name=subj_in.name,
        department=subj_in.department,
        faculty_id=current_user.id,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ------------------------------------------------------------------
# CLASS SESSION LIFECYCLE
# ------------------------------------------------------------------
@router.get("", response_model=List[SessionResponse])
def list_sessions(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ClassSession)
    if status_filter:
        query = query.filter(ClassSession.status == status_filter)
    sessions = query.order_by(ClassSession.start_time.desc()).all()

    results = []
    for s in sessions:
        results.append(
            SessionResponse(
                id=s.id,
                subject_id=s.subject_id,
                subject_name=s.subject.name if s.subject else "N/A",
                subject_code=s.subject.code if s.subject else "N/A",
                room=s.room,
                start_time=s.start_time,
                end_time=s.end_time,
                status=s.status,
                checkpoint_interval_mins=s.checkpoint_interval_mins,
                min_presence_percentage=s.min_presence_percentage,
                created_at=s.created_at,
            )
        )
    return results


@router.get("/active", response_model=Optional[SessionResponse])
def get_active_session(db: Session = Depends(get_db)):
    """
    Returns the currently active session where the camera should record attendance.
    """
    now = datetime.datetime.utcnow()
    # Find sessions marked explicitly active OR scheduled within the current time window
    active_session = (
        db.query(ClassSession)
        .filter(
            (ClassSession.status == "active")
            | (
                (ClassSession.status == "scheduled")
                & (ClassSession.start_time <= now)
                & (ClassSession.end_time >= now)
            )
        )
        .first()
    )

    if not active_session:
        return None

    return SessionResponse(
        id=active_session.id,
        subject_id=active_session.subject_id,
        subject_name=active_session.subject.name if active_session.subject else "N/A",
        subject_code=active_session.subject.code if active_session.subject else "N/A",
        room=active_session.room,
        start_time=active_session.start_time,
        end_time=active_session.end_time,
        status=active_session.status,
        checkpoint_interval_mins=active_session.checkpoint_interval_mins,
        min_presence_percentage=active_session.min_presence_percentage,
        created_at=active_session.created_at,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_in: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Schedules a new class session with custom continuous presence checkpoints."""
    subject = db.query(Subject).filter(Subject.id == session_in.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    new_session = ClassSession(
        subject_id=session_in.subject_id,
        faculty_id=current_user.id,
        room=session_in.room,
        start_time=session_in.start_time,
        end_time=session_in.end_time,
        status="scheduled",
        checkpoint_interval_mins=session_in.checkpoint_interval_mins,
        min_presence_percentage=session_in.min_presence_percentage,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return SessionResponse(
        id=new_session.id,
        subject_id=new_session.subject_id,
        subject_name=subject.name,
        subject_code=subject.code,
        room=new_session.room,
        start_time=new_session.start_time,
        end_time=new_session.end_time,
        status=new_session.status,
        checkpoint_interval_mins=new_session.checkpoint_interval_mins,
        min_presence_percentage=new_session.min_presence_percentage,
        created_at=new_session.created_at,
    )


@router.post("/{session_id}/start")
def start_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Faculty initiates active classroom attendance with pre-lecture buffer grandfathering."""
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.datetime.utcnow()
    session.status = "active"
    # Anchor active start_time to current moment
    session.start_time = now
    db.commit()

    # Re-evaluate all pre-scanned students in this session so their presence is 100% in Interval 0
    from backend.app.models import Attendance
    from backend.app.services.presence import calculate_session_presence

    existing_records = db.query(Attendance).filter(Attendance.session_id == session.id).all()
    for rec in existing_records:
        score, status_str, det, tot, avg_vis, occ = calculate_session_presence(
            db, session.id, rec.student_id
        )
        rec.presence_score = score
        rec.status = status_str
        rec.checkpoints_detected = det
        rec.total_checkpoints = tot
        rec.face_visibility_score = avg_vis
        rec.occlusion_count = occ
    db.commit()

    return {
        "success": True,
        "message": f"Class session '{session.id}' is now ACTIVE. {len(existing_records)} pre-arrival check-ins retained.",
        "pre_scanned_students": len(existing_records),
    }


@router.post("/{session_id}/end")
def end_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Faculty concludes lecture; finalizes presence scoring."""
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "completed"
    session.end_time = datetime.datetime.utcnow()
    db.commit()
    return {"success": True, "message": f"Class session '{session.id}' completed and attendance finalized."}
