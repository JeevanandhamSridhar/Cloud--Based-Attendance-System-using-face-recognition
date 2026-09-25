import base64
import datetime
import json
import numpy as np
import cv2
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models import (
    Attendance,
    AttendanceEvent,
    ClassSession,
    DailyCampusAttendance,
    FaceEmbedding,
    Student,
    User,
)
from backend.app.schemas import (
    AttendanceRecordResponse,
    DailyCampusAttendanceResponse,
    DetectedStudentMatch,
    ScanFrameRequest,
    ScanResultResponse,
    VerifyAttendanceRequest,
)
from backend.app.security import get_current_user, require_faculty_or_admin
from backend.app.services.presence import update_student_attendance_record
from core.face_engine import FaceEngine
from core.matcher import FaceMatcher

router = APIRouter(prefix="/attendance", tags=["Attendance & Facial Inference"])

# Cached instance
_face_engine = None


def get_face_engine():
    global _face_engine
    if _face_engine is None:
        _face_engine = FaceEngine()
    return _face_engine


def find_best_embedding_match(
    db: Session, query_emb: np.ndarray, threshold: float = 0.48
):
    """
    Finds closest student by comparing query vector against enrolled students.
    Uses cached vectors with L2 dot product cosine similarity.
    """
    q = query_emb.astype(np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm > 1e-6:
        q = q / q_norm

    # Fetch all stored embeddings
    all_embeddings = db.query(FaceEmbedding).all()
    best_student = None
    best_sim = -1.0

    for item in all_embeddings:
        try:
            vec = np.array(json.loads(item.embedding_json), dtype=np.float32)
            v_norm = np.linalg.norm(vec)
            if v_norm > 1e-6:
                vec = vec / v_norm
            sim = float(np.dot(q, vec))
            if sim > best_sim:
                best_sim = sim
                best_student = item.student
        except Exception:
            continue

    if best_sim >= threshold and best_student is not None:
        return best_student, best_sim
    return None, max(0.0, best_sim)


def record_daily_campus_attendance(
    db: Session, student_id: str, sim: float, entry_gate: str = "Main Campus Gate"
) -> DailyCampusAttendance:
    """Records or updates daily campus presence at the college entrance or classroom."""
    now = datetime.datetime.utcnow()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    rec = (
        db.query(DailyCampusAttendance)
        .filter(
            DailyCampusAttendance.student_id == student_id,
            DailyCampusAttendance.date == today_midnight,
        )
        .first()
    )
    if not rec:
        rec = DailyCampusAttendance(
            student_id=student_id,
            date=today_midnight,
            status="present",
            first_entry_time=now,
            last_seen_time=now,
            entry_gate=entry_gate,
            confidence_avg=sim,
            liveness_verified=True,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
    else:
        rec.last_seen_time = now
        rec.confidence_avg = round((rec.confidence_avg + sim) / 2.0, 3)
        db.commit()
        db.refresh(rec)
    return rec


@router.post("/scan-frame", response_model=ScanResultResponse)
def scan_frame_and_mark_attendance(
    payload: ScanFrameRequest,
    db: Session = Depends(get_db),
):
    """
    Core AI Inference Endpoint:
    1. Supports Dual-Tier: Campus Gate Entry (`campus_gate`) vs Course Lecture Sessions.
    2. Runs ArcFace detection & embedding extraction on the frame.
    3. Performs vector similarity matching against registered students.
    4. Evaluates liveness, handkerchief/mask occlusion, and updates AttenFace continuous presence score.
    """
    # 1. Verify Session or Campus Gate Mode
    is_campus_gate = (
        payload.session_id.lower() in ["campus_gate", "campus_entrance", "gate_01"]
        or payload.session_id.lower().startswith("campus_")
    )
    session = None
    if not is_campus_gate:
        session = db.query(ClassSession).filter(ClassSession.id == payload.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Class session not found")
        if session.status == "completed" or session.status == "cancelled":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot record attendance: session is already {session.status}.",
            )

    # 2. Decode Frame
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]
        img_bytes = base64.b64decode(raw_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Failed to decode image buffer")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

    # 3. Detect Faces & Extract 512-D ArcFace Embeddings
    engine = get_face_engine()
    detected_faces = engine.extract_faces(frame)

    matches_result = []
    students_recognized_count = 0

    for face in detected_faces:
        bbox = face["bbox"]
        emb = face["embedding"]
        det_score = face["det_score"]
        is_occluded = face.get("is_occluded", False)
        occlusion_type = face.get("occlusion_type", "unobstructed")
        vis_score = face.get("visibility_score", 1.0)

        # Adaptive threshold: lower face covered by kerchief/mask lowers embedding similarity
        # Periocular (upper-face) matching threshold is 0.38 for occluded faces
        eval_threshold = 0.38 if is_occluded else settings.FACE_MATCH_THRESHOLD

        student, sim = find_best_embedding_match(
            db, emb, threshold=eval_threshold
        )
        conf_pct = round(sim * 100, 1)

        is_live = payload.client_is_live
        ear_val = payload.ear_value

        if student is not None:
            students_recognized_count += 1

            # Auto-record College Campus Presence for today in both modes
            gate_name = "Main Campus Gate" if is_campus_gate else f"Classroom ({session.room})"
            record_daily_campus_attendance(db, student.id, sim, entry_gate=gate_name)

            if not is_live:
                match_status = "spoof_rejected"
                liveness_str = "REJECTED (Spoof / Screen Detected)"
            elif is_campus_gate:
                match_status = "campus_present"
                liveness_str = "PASS (College Campus Entry Recorded)"
            elif is_occluded:
                # Student detected with handkerchief / mask / wiping face
                match_status = "present_occluded"
                liveness_str = f"PASS (Kerchief/Mask - {int(vis_score * 100)}% Visible)"
            elif sim < settings.FLAGGED_REVIEW_THRESHOLD:
                # Borderline match (e.g. 50% - 60%) -> Flag for faculty review
                match_status = "flagged"
                liveness_str = "PASS (Flagged for Review)"
            else:
                match_status = "present"
                liveness_str = "PASS (Real Person - Unobstructed)"

            # If classroom session, log lecture event and update continuous presence
            if not is_campus_gate and session and is_live:
                event = AttendanceEvent(
                    session_id=session.id,
                    student_id=student.id,
                    confidence=sim,
                    liveness_score=1.0,
                    ear_value=ear_val,
                    is_live=True,
                    is_occluded=is_occluded,
                    occlusion_type=occlusion_type,
                    visibility_score=vis_score,
                    camera_id=payload.camera_id,
                )
                db.add(event)
                db.commit()

                # Update continuous presence score with occlusion visibility tracking
                att_record = update_student_attendance_record(
                    db,
                    session.id,
                    student.id,
                    sim,
                    is_occluded=is_occluded,
                    visibility_score=vis_score,
                )
                if match_status == "flagged":
                    att_record.status = "flagged_review"
                    db.commit()

            matches_result.append(
                DetectedStudentMatch(
                    student_id=student.id,
                    student_code=student.student_id,
                    student_name=student.name,
                    confidence=conf_pct,
                    is_live=is_live,
                    liveness_status=liveness_str,
                    ear=ear_val,
                    bbox=list(bbox),
                    status=match_status,
                    is_occluded=is_occluded,
                    occlusion_type=occlusion_type,
                    visibility_score=vis_score,
                )
            )
        else:
            matches_result.append(
                DetectedStudentMatch(
                    student_id=None,
                    student_code=None,
                    student_name=None,
                    confidence=conf_pct,
                    is_live=is_live,
                    liveness_status="Unknown Face" if not is_occluded else "Unknown (Face Occluded)",
                    ear=ear_val,
                    bbox=list(bbox),
                    status="unknown",
                    is_occluded=is_occluded,
                    occlusion_type=occlusion_type,
                    visibility_score=vis_score,
                )
            )

    return ScanResultResponse(
        session_id=session.id if session else payload.session_id,
        faces_detected=len(detected_faces),
        students_recognized=students_recognized_count,
        matches=matches_result,
    )


@router.get("/session/{session_id}", response_model=List[AttendanceRecordResponse])
def get_session_attendance(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves computed attendance records and presence scores for a session."""
    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    results = []
    for r in records:
        results.append(
            AttendanceRecordResponse(
                id=r.id,
                session_id=r.session_id,
                student_id=r.student_id,
                student_code=r.student.student_id,
                student_name=r.student.name,
                department=r.student.department,
                status=r.status,
                presence_score=r.presence_score,
                confidence_avg=r.confidence_avg,
                checkpoints_detected=r.checkpoints_detected,
                total_checkpoints=r.total_checkpoints,
                face_visibility_score=getattr(r, "face_visibility_score", 100.0) or 100.0,
                occlusion_count=getattr(r, "occlusion_count", 0) or 0,
                first_seen=r.first_seen,
                last_seen=r.last_seen,
                verified_by_faculty=r.verified_by_faculty,
            )
        )
    return results


@router.get("/review-queue/{session_id}", response_model=List[AttendanceRecordResponse])
def get_flagged_review_queue(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Fetches borderline matches (< 60% confidence) requiring faculty confirmation."""
    flagged = (
        db.query(Attendance)
        .filter(
            Attendance.session_id == session_id,
            Attendance.status == "flagged_review",
        )
        .all()
    )
    results = []
    for r in flagged:
        results.append(
            AttendanceRecordResponse(
                id=r.id,
                session_id=r.session_id,
                student_id=r.student_id,
                student_code=r.student.student_id,
                student_name=r.student.name,
                department=r.student.department,
                status=r.status,
                presence_score=r.presence_score,
                confidence_avg=r.confidence_avg,
                checkpoints_detected=r.checkpoints_detected,
                total_checkpoints=r.total_checkpoints,
                face_visibility_score=getattr(r, "face_visibility_score", 100.0) or 100.0,
                occlusion_count=getattr(r, "occlusion_count", 0) or 0,
                first_seen=r.first_seen,
                last_seen=r.last_seen,
                verified_by_faculty=r.verified_by_faculty,
            )
        )
    return results


@router.post("/verify/{attendance_id}")
def verify_flagged_attendance(
    attendance_id: str,
    payload: VerifyAttendanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Faculty approves or rejects a flagged attendance record."""
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.verified_by_faculty = True
    record.faculty_notes = payload.notes
    if payload.approved:
        record.status = "present" if record.presence_score >= 50.0 else "partial"
    else:
        record.status = "absent"

    db.commit()
    return {
        "success": True,
        "message": f"Attendance record updated to '{record.status}'.",
        "status": record.status,
    }


@router.get("/campus/today")
def get_today_campus_attendance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all students' campus gate attendance status for today."""
    now = datetime.datetime.utcnow()
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    students = db.query(Student).filter(Student.status == "active").all()
    campus_records = {
        c.student_id: c
        for c in db.query(DailyCampusAttendance)
        .filter(DailyCampusAttendance.date == today_midnight)
        .all()
    }

    result = []
    for st in students:
        rec = campus_records.get(st.id)
        if rec:
            result.append(
                {
                    "student_id": st.id,
                    "student_code": st.student_id,
                    "student_name": st.name,
                    "department": st.department,
                    "status": rec.status,
                    "first_entry_time": rec.first_entry_time,
                    "last_seen_time": rec.last_seen_time,
                    "entry_gate": rec.entry_gate,
                    "confidence_avg": round(rec.confidence_avg * 100, 1) if rec.confidence_avg <= 1.0 else rec.confidence_avg,
                    "liveness_verified": rec.liveness_verified,
                }
            )
        else:
            result.append(
                {
                    "student_id": st.id,
                    "student_code": st.student_id,
                    "student_name": st.name,
                    "department": st.department,
                    "status": "absent",
                    "first_entry_time": None,
                    "last_seen_time": None,
                    "entry_gate": "Not Entered",
                    "confidence_avg": 0.0,
                    "liveness_verified": False,
                }
            )

    return result
