import datetime
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import Base, SessionLocal, engine
from backend.app.models import ClassSession, FaceEmbedding, Student, Subject, User

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Reset tables for a clean test run and ensure default faculty is always seeded."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from backend.app.security import get_password_hash
    db = SessionLocal()
    try:
        user = User(
            email="faculty@college.edu",
            password_hash=get_password_hash("Password123!"),
            full_name="Dr. Alexander Reed",
            role="faculty",
        )
        db.add(user)
        db.commit()
    finally:
        db.close()
    yield
    # At teardown, ensure clean DB with default faculty, CS301, and zero students
    db = SessionLocal()
    try:
        db.query(Student).delete()
        db.commit()
        user = db.query(User).filter(User.email == "faculty@college.edu").first()
        if not user:
            user = User(
                email="faculty@college.edu",
                password_hash=get_password_hash("Password123!"),
                full_name="Dr. Alexander Reed",
                role="faculty",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        if not db.query(Subject).filter(Subject.code == "CS301").first():
            subj = Subject(code="CS301", name="Data Structures & Algorithms", department="Computer Science", faculty_id=user.id)
            db.add(subj)
            db.commit()
    finally:
        db.close()
    try:
        with open("data/embeddings.json", "w", encoding="utf-8") as ef:
            ef.write("{}\n")
    except Exception:
        pass


def test_health_and_root():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert "Cloud-Based Smart Attendance" in root_res.json()["project"]


def test_auth_and_jwt_workflow():
    # 1. Register faculty user
    register_payload = {
        "email": "dr.smith@college.edu",
        "password": "SecretPassword123!",
        "full_name": "Dr. Smith",
        "role": "faculty",
    }
    reg_res = client.post("/api/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == "dr.smith@college.edu"

    # 2. Login to obtain JWT
    login_payload = {
        "email": "dr.smith@college.edu",
        "password": "SecretPassword123!",
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Access protected route with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Dr. Smith"


def test_student_management_and_embedding_enrollment():
    # Setup auth token
    client.post(
        "/api/auth/register",
        json={
            "email": "admin@college.edu",
            "password": "Password123!",
            "full_name": "Administrator",
            "role": "admin",
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "admin@college.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Create Student
    student_payload = {
        "student_id": "23CS101",
        "name": "Priya Sharma",
        "department": "Computer Science",
        "year": 3,
        "section": "A",
        "email": "priya.cs@college.edu",
    }
    create_res = client.post("/api/students", json=student_payload, headers=headers)
    assert create_res.status_code == 201
    student = create_res.json()
    assert student["student_id"] == "23CS101"
    assert student["has_face_registered"] is False

    # 2. Enroll a 512-D ArcFace embedding vector
    np.random.seed(99)
    sample_vec = np.random.randn(512).astype(np.float32)
    sample_vec = sample_vec / np.linalg.norm(sample_vec)

    enroll_payload = {"embedding": sample_vec.tolist()}
    enroll_res = client.post(
        f"/api/students/{student['id']}/enroll-face",
        json=enroll_payload,
        headers=headers,
    )
    assert enroll_res.status_code == 200
    assert enroll_res.json()["success"] is True

    # 3. Verify student now shows has_face_registered = True
    get_res = client.get(f"/api/students/{student['id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["has_face_registered"] is True

    # 4. Delete the student and verify permanent removal
    del_res = client.delete(f"/api/students/{student['id']}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 5. Verify student is 404 Not Found and not listed
    check_del = client.get(f"/api/students/{student['id']}", headers=headers)
    assert check_del.status_code == 404

    list_res = client.get("/api/students", headers=headers)
    assert list_res.status_code == 200
    assert all(s["student_id"] != "23CS101" for s in list_res.json())

    # 6. Verify matcher and embeddings.json no longer contain the student
    from core.matcher import FaceMatcher
    matcher = FaceMatcher()
    assert "23CS101" not in matcher.students



def test_session_lifecycle_and_attendance_flow():
    # Setup faculty
    client.post(
        "/api/auth/register",
        json={
            "email": "faculty@college.edu",
            "password": "Password123!",
            "full_name": "Prof. Rao",
            "role": "faculty",
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "faculty@college.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Create Subject
    subj_res = client.post(
        "/api/sessions/subjects",
        json={"code": "CS302", "name": "Operating Systems", "department": "CS"},
        headers=headers,
    )
    assert subj_res.status_code == 201
    subject_id = subj_res.json()["id"]

    # 2. Create Class Session
    now = datetime.datetime.utcnow()
    session_payload = {
        "subject_id": subject_id,
        "room": "Lab-02",
        "start_time": now.isoformat(),
        "end_time": (now + datetime.timedelta(minutes=60)).isoformat(),
        "checkpoint_interval_mins": 5,
        "min_presence_percentage": 75.0,
    }
    sess_res = client.post("/api/sessions", json=session_payload, headers=headers)
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 3. Start Session
    start_res = client.post(f"/api/sessions/{session_id}/start", headers=headers)
    assert start_res.status_code == 200

    # 4. Check active session endpoint
    active_res = client.get("/api/sessions/active")
    assert active_res.status_code == 200
    assert active_res.json()["id"] == session_id

    # 5. Check empty attendance list initially
    att_res = client.get(f"/api/attendance/session/{session_id}", headers=headers)
    assert att_res.status_code == 200
    assert len(att_res.json()) == 0

    # 6. End Session
    end_res = client.post(f"/api/sessions/{session_id}/end", headers=headers)
    assert end_res.status_code == 200


def test_analytics_and_csv_export():
    client.post(
        "/api/auth/register",
        json={
            "email": "dean@college.edu",
            "password": "Password123!",
            "full_name": "Dean Academic",
            "role": "admin",
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": "dean@college.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 1. Create a subject & session
    subj = client.post(
        "/api/sessions/subjects",
        json={"code": "CS303", "name": "Database Systems", "department": "CS"},
        headers=headers,
    ).json()

    now = datetime.datetime.utcnow()
    sess = client.post(
        "/api/sessions",
        json={
            "subject_id": subj["id"],
            "room": "Room-101",
            "start_time": now.isoformat(),
            "end_time": (now + datetime.timedelta(minutes=50)).isoformat(),
        },
        headers=headers,
    ).json()

    # 2. Check Dashboard Summary
    dash_res = client.get("/api/analytics/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert "total_enrolled_students" in dash_data
    assert "average_presence_percentage" in dash_data

    # 3. Check CSV Export
    csv_res = client.get(f"/api/analytics/export/csv/{sess['id']}", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "INSTITUTIONAL SMART ATTENDANCE REPORT" in csv_res.text


def test_campus_gate_attendance_and_bunking_audit():
    # 1. Login
    login_res = client.post(
        "/api/auth/login",
        json={"email": "faculty@college.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # 2. Query today campus attendance
    res = client.get("/api/attendance/campus/today", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 3. Create subject & session for bunking audit test
    subj = client.post(
        "/api/sessions/subjects",
        json={"code": "CS305", "name": "Operating Systems", "department": "CS"},
        headers=headers,
    ).json()

    now = datetime.datetime.utcnow()
    sess = client.post(
        "/api/sessions",
        json={
            "subject_id": subj["id"],
            "room": "Room-202",
            "start_time": now.isoformat(),
            "end_time": (now + datetime.timedelta(minutes=60)).isoformat(),
        },
        headers=headers,
    ).json()

    # 4. Check bunking report
    bunk_res = client.get(f"/api/analytics/bunking-report?session_id={sess['id']}", headers=headers)
    assert bunk_res.status_code == 200
    audit_data = bunk_res.json()
    assert isinstance(audit_data, list)
