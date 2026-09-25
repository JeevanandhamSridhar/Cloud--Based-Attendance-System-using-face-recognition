import datetime
from typing import Dict, Tuple
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models import Attendance, AttendanceEvent, ClassSession, Student


def calculate_session_presence(
    db: Session, session_id: str, student_id: str
) -> Tuple[float, str, int, int, float, int]:
    """
    Computes AttenFace continuous presence score for a student in a class session:
    - Active Session: Evaluates against elapsed checkpoints so far (prevents attendance drop mid-lecture).
    - Completed Session: Evaluates against total scheduled checkpoints.
    - Early Arrival Grace: Scans up to 15 minutes before lecture starts are grandfathered into interval 0.
    - Occlusion Tolerance: Wiping face or wearing a kerchief/mask maintains continuous presence.

    Returns:
        (presence_score, status_str, checkpoints_detected, total_checkpoints, face_visibility_avg, occlusion_count)
    """
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        return 0.0, "absent", 0, 1, 100.0, 0

    now = datetime.datetime.utcnow()

    # Total planned checkpoints based on session duration and interval
    duration_mins = max(
        5, int((session.end_time - session.start_time).total_seconds() / 60)
    )
    interval = max(1, session.checkpoint_interval_mins)
    total_expected_checkpoints = max(1, duration_mins // interval)

    # Dynamic Denominator: during active session, evaluate against checkpoints elapsed up to now
    if session.status == "active":
        elapsed_mins = max(1.0, (now - session.start_time).total_seconds() / 60.0)
        elapsed_intervals = max(1, int(elapsed_mins // interval) + 1)
        total_eval_checkpoints = min(elapsed_intervals, total_expected_checkpoints)
    else:
        total_eval_checkpoints = total_expected_checkpoints

    # Fetch all verified live events for this student in this session
    events = (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.session_id == session_id,
            AttendanceEvent.student_id == student_id,
            AttendanceEvent.is_live.is_(True),
        )
        .order_by(AttendanceEvent.timestamp.asc())
        .all()
    )

    if not events:
        return 0.0, "absent", 0, total_eval_checkpoints, 100.0, 0

    detected_intervals = set()
    confidences = []
    visibility_scores = []
    occlusion_count = 0

    for ev in events:
        confidences.append(ev.confidence)
        vis = getattr(ev, "visibility_score", 1.0)
        if vis is not None:
            visibility_scores.append(float(vis))
        if getattr(ev, "is_occluded", False):
            occlusion_count += 1

        # Delta minutes from session start
        delta_mins = (ev.timestamp - session.start_time).total_seconds() / 60.0
        # Grandfather pre-lecture check-ins (up to 15 mins prior) into bucket 0
        if delta_mins < 0:
            interval_bucket = 0
        else:
            interval_bucket = int(delta_mins // interval)
        detected_intervals.add(interval_bucket)

    checkpoints_detected = min(len(detected_intervals), total_eval_checkpoints)
    presence_score = round(
        (checkpoints_detected / float(total_eval_checkpoints)) * 100.0, 1
    )
    presence_score = min(100.0, max(0.0, presence_score))

    # Face Visibility Average (% of time face was fully clear vs occluded)
    if visibility_scores:
        avg_visibility = round(float(np.mean(visibility_scores)) * 100.0, 1)
    else:
        avg_visibility = 100.0

    # Evaluate institutional attendance policy with Grace Window
    # If student was detected recently (< 5 mins), guarantee they are marked present
    last_event_time = events[-1].timestamp
    secs_since_last = (now - last_event_time).total_seconds()
    is_recently_active = secs_since_last <= 300.0  # 5-minute active grace window

    min_thresh = session.min_presence_percentage
    if presence_score >= min_thresh or (is_recently_active and checkpoints_detected >= 1):
        status_str = "present"
    elif presence_score >= 50.0:
        status_str = "partial"
    else:
        status_str = "absent"

    return (
        presence_score,
        status_str,
        checkpoints_detected,
        total_eval_checkpoints,
        avg_visibility,
        occlusion_count,
    )


def update_student_attendance_record(
    db: Session,
    session_id: str,
    student_id: str,
    new_confidence: float,
    is_occluded: bool = False,
    visibility_score: float = 1.0,
) -> Attendance:
    """
    Updates or creates the Attendance record when a new detection occurs.
    Includes face visibility percentage and occlusion tracking.
    """
    record = (
        db.query(Attendance)
        .filter(Attendance.session_id == session_id, Attendance.student_id == student_id)
        .first()
    )

    now = datetime.datetime.utcnow()

    score, status_str, detected, total, avg_vis, occ_count = calculate_session_presence(
        db, session_id, student_id
    )

    if not record:
        record = Attendance(
            session_id=session_id,
            student_id=student_id,
            status=status_str,
            presence_score=score,
            confidence_avg=round(new_confidence * 100, 1),
            first_seen=now,
            last_seen=now,
            checkpoints_detected=detected,
            total_checkpoints=total,
            face_visibility_score=avg_vis,
            occlusion_count=occ_count,
        )
        db.add(record)
    else:
        record.last_seen = now
        record.presence_score = score
        record.status = status_str
        record.checkpoints_detected = detected
        record.total_checkpoints = total
        record.face_visibility_score = avg_vis
        record.occlusion_count = occ_count
        # Running average of confidence
        record.confidence_avg = round(
            (record.confidence_avg * 0.7) + ((new_confidence * 100) * 0.3), 1
        )

    db.commit()
    db.refresh(record)
    return record
