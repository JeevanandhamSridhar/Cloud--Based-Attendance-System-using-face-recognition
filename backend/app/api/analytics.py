import csv
import datetime
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Attendance, ClassSession, DailyCampusAttendance, Student, User
from backend.app.schemas import (
    BunkingAuditItem,
    DashboardSummaryResponse,
    LowAttendanceAlert,
)
from backend.app.security import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])


@router.get("/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computes institutional high-level KPIs for the faculty dashboard:
    - Total student count
    - Active sessions
    - Today's presence distribution
    - Average presence percentage
    - Students with attendance < 75%
    """
    today_start = datetime.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    total_students = db.query(Student).count()
    active_sessions = (
        db.query(ClassSession).filter(ClassSession.status == "active").count()
    )

    today_attendances = (
        db.query(Attendance).filter(Attendance.created_at >= today_start).all()
    )

    today_present = sum(1 for a in today_attendances if a.status == "present")
    today_partial = sum(1 for a in today_attendances if a.status == "partial")
    today_absent = sum(1 for a in today_attendances if a.status == "absent")

    avg_presence = 0.0
    if today_attendances:
        avg_presence = round(
            sum(a.presence_score for a in today_attendances) / len(today_attendances), 1
        )

    # Calculate low attendance students across all historical records (< 75%)
    all_students = db.query(Student).all()
    low_attendance_list = []

    for s in all_students:
        s_records = db.query(Attendance).filter(Attendance.student_id == s.id).all()
        if s_records:
            present_count = sum(1 for r in s_records if r.status == "present")
            att_pct = round((present_count / float(len(s_records))) * 100.0, 1)
            if att_pct < 75.0:
                low_attendance_list.append(
                    LowAttendanceAlert(
                        student_id=s.id,
                        student_code=s.student_id,
                        name=s.name,
                        department=s.department,
                        attendance_pct=att_pct,
                    )
                )

    today_campus_entries = (
        db.query(DailyCampusAttendance)
        .filter(DailyCampusAttendance.date == today_start, DailyCampusAttendance.status == "present")
        .all()
    )
    today_campus_entry_count = len(today_campus_entries)
    campus_student_ids = {c.student_id for c in today_campus_entries}

    # Bunking count: On campus today, but absent in a class session held today
    bunking_count = (
        db.query(Attendance)
        .filter(
            Attendance.created_at >= today_start,
            Attendance.status == "absent",
            Attendance.student_id.in_(campus_student_ids) if campus_student_ids else False,
        )
        .distinct(Attendance.student_id)
        .count()
        if campus_student_ids
        else 0
    )

    return DashboardSummaryResponse(
        total_enrolled_students=total_students,
        active_sessions_count=active_sessions,
        today_total_attendances=len(today_attendances),
        today_present_count=today_present,
        today_partial_count=today_partial,
        today_absent_count=today_absent,
        average_presence_percentage=avg_presence,
        low_attendance_students=low_attendance_list,
        today_campus_entry_count=today_campus_entry_count,
        bunking_flagged_count=bunking_count,
    )


@router.get("/bunking-report", response_model=List[BunkingAuditItem])
def get_bunking_audit_report(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dual-Tier Truancy Analysis Endpoint:
    Correlates Gate/Campus Attendance vs Classroom Lecture Attendance for each student.
    Detects students who entered college gate but skipped the lecture!
    """
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_date = session.start_time.replace(hour=0, minute=0, second=0, microsecond=0)

    # Campus gate records for this date
    campus_records = {
        c.student_id: c
        for c in db.query(DailyCampusAttendance)
        .filter(DailyCampusAttendance.date == session_date)
        .all()
    }

    # Class attendance records for this session
    class_records = {
        a.student_id: a
        for a in db.query(Attendance)
        .filter(Attendance.session_id == session_id)
        .all()
    }

    students = db.query(Student).filter(Student.status == "active").all()
    audit_results = []

    for st in students:
        c_rec = campus_records.get(st.id)
        a_rec = class_records.get(st.id)

        is_on_campus = bool(c_rec and c_rec.status == "present")
        class_status = a_rec.status if a_rec else "absent"
        presence_score = a_rec.presence_score if a_rec else 0.0

        if is_on_campus and class_status in ["present", "partial"]:
            classification = "ATTENDING_CLASS"
            badge = "Normal (On Campus & In Class)"
        elif is_on_campus and class_status == "absent":
            classification = "BUNKING_CLASS"
            badge = "TRUANCY FLAGGED: On Campus, Bunked Lecture!"
        elif not is_on_campus and class_status == "absent":
            classification = "FULL_DAY_ABSENT"
            badge = "Full Day Absent (Never Entered College)"
        else:
            classification = "ATTENDING_CLASS"
            badge = "In Class (Campus Gate Auto-Credited)"

        audit_results.append(
            BunkingAuditItem(
                student_id=st.id,
                student_code=st.student_id,
                student_name=st.name,
                department=st.department,
                campus_status="present_on_campus" if is_on_campus else "absent_from_campus",
                campus_entry_time=c_rec.first_entry_time if c_rec else None,
                class_status=class_status,
                class_presence_score=presence_score,
                classification=classification,
                discrepancy_badge=badge,
            )
        )

    return audit_results


@router.get("/export/csv/{session_id}")
def export_session_attendance_csv(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates a structured institutional CSV report with Campus vs Class Truancy breakdown.
    """
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session_date = session.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    campus_records = {
        c.student_id: c
        for c in db.query(DailyCampusAttendance)
        .filter(DailyCampusAttendance.date == session_date)
        .all()
    }

    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header section
    writer.writerow(["INSTITUTIONAL SMART ATTENDANCE REPORT - CAMPUS & TRUANCY AUDIT"])
    writer.writerow(["Subject", session.subject.name if session.subject else "N/A"])
    writer.writerow(["Course Code", session.subject.code if session.subject else "N/A"])
    writer.writerow(["Room", session.room])
    writer.writerow(["Date", session.start_time.strftime("%Y-%m-%d %H:%M")])
    writer.writerow(["Generated At", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")])
    writer.writerow([])

    # Table columns
    writer.writerow([
        "Student ID",
        "Student Name",
        "Department",
        "Class Attendance Status",
        "Class Presence (%)",
        "Campus Gate Status",
        "Campus Entry Time",
        "Truancy / Discrepancy Classification",
        "Face Visibility (%)",
        "Occlusion Events",
        "Confidence Avg (%)",
        "Checkpoints Detected",
        "Total Checkpoints",
        "First Seen in Class",
        "Last Seen in Class",
        "Faculty Verified",
    ])

    for r in records:
        c_rec = campus_records.get(r.student_id)
        is_on_campus = bool(c_rec and c_rec.status == "present")

        if is_on_campus and r.status in ["present", "partial"]:
            truancy_tag = "Normal (On Campus & In Class)"
        elif is_on_campus and r.status == "absent":
            truancy_tag = "TRUANCY FLAGGED: On Campus, Bunked Lecture!"
        elif not is_on_campus and r.status == "absent":
            truancy_tag = "Full Day Absent (Never Entered College)"
        else:
            truancy_tag = "In Class (Gate Auto-Credited)"

        campus_status_str = f"PRESENT ({c_rec.first_entry_time.strftime('%H:%M:%S')})" if is_on_campus and c_rec.first_entry_time else ("PRESENT" if is_on_campus else "ABSENT FROM CAMPUS")
        campus_entry_str = c_rec.first_entry_time.strftime("%H:%M:%S") if c_rec and c_rec.first_entry_time else "N/A"

        writer.writerow([
            r.student.student_id,
            r.student.name,
            r.student.department,
            r.status.upper(),
            f"{r.presence_score:.1f}%",
            campus_status_str,
            campus_entry_str,
            truancy_tag,
            f"{getattr(r, 'face_visibility_score', 100.0) or 100.0:.1f}%",
            getattr(r, "occlusion_count", 0) or 0,
            f"{r.confidence_avg:.1f}%",
            r.checkpoints_detected,
            r.total_checkpoints,
            r.first_seen.strftime("%H:%M:%S") if r.first_seen else "N/A",
            r.last_seen.strftime("%H:%M:%S") if r.last_seen else "N/A",
            "YES" if r.verified_by_faculty else "NO",
        ])

    csv_data = output.getvalue()
    filename = f"institutional_attendance_{session.subject.code if session.subject else 'session'}_{session_id[:8]}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
