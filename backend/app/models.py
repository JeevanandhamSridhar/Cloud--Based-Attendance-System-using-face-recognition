import datetime
import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, default="faculty")  # admin, faculty, student
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    sessions = relationship("ClassSession", back_populates="faculty")
    subjects = relationship("Subject", back_populates="faculty")


class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    department = Column(String(100), default="Computer Science")
    year = Column(Integer, default=3)
    section = Column(String(10), default="A")
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    embeddings = relationship("FaceEmbedding", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    campus_attendances = relationship("DailyCampusAttendance", back_populates="student", cascade="all, delete-orphan")


class FaceEmbedding(Base):
    __tablename__ = "face_embeddings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    # Stored as serialized JSON string representing the 512-D float list
    # Works natively across both SQLite and PostgreSQL
    embedding_json = Column(Text, nullable=False)
    model_version = Column(String(50), default="ArcFace_buffalo_sc_512")
    is_primary = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="embeddings")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    department = Column(String(100), default="Computer Science")
    faculty_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    faculty = relationship("User", back_populates="subjects")
    sessions = relationship("ClassSession", back_populates="subject", cascade="all, delete-orphan")


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room = Column(String(50), default="Lab-01")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(50), default="scheduled")  # scheduled, active, completed, cancelled
    checkpoint_interval_mins = Column(Integer, default=5)
    min_presence_percentage = Column(Float, default=75.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    subject = relationship("Subject", back_populates="sessions")
    faculty = relationship("User", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")
    events = relationship("AttendanceEvent", back_populates="session", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_session_student"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="absent")  # present, partial, absent, flagged_review
    presence_score = Column(Float, default=0.0)
    confidence_avg = Column(Float, default=0.0)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    checkpoints_detected = Column(Integer, default=0)
    total_checkpoints = Column(Integer, default=1)
    face_visibility_score = Column(Float, default=100.0)  # % of time face was fully clear vs occluded
    occlusion_count = Column(Integer, default=0)  # Occurrences of handkerchief/mask/wiping
    verified_by_faculty = Column(Boolean, default=False)
    faculty_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    session = relationship("ClassSession", back_populates="attendances")
    student = relationship("Student", back_populates="attendances")
    events = relationship("AttendanceEvent", back_populates="attendance", cascade="all, delete-orphan")


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attendance_id = Column(String(36), ForeignKey("attendance.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(36), ForeignKey("class_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    confidence = Column(Float, nullable=False)
    liveness_score = Column(Float, default=1.0)
    ear_value = Column(Float, nullable=True)
    is_live = Column(Boolean, default=True)
    is_occluded = Column(Boolean, default=False)
    occlusion_type = Column(String(50), default="unobstructed")
    visibility_score = Column(Float, default=1.0)
    camera_id = Column(String(50), default="WEBCAM-01")

    attendance = relationship("Attendance", back_populates="events")
    session = relationship("ClassSession", back_populates="events")


class DailyCampusAttendance(Base):
    __tablename__ = "daily_campus_attendance"
    __table_args__ = (UniqueConstraint("student_id", "date", name="uq_student_campus_date"),)

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)  # Midnight UTC anchor for the day
    status = Column(String(50), default="present")  # present, late, absent
    first_entry_time = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen_time = Column(DateTime, default=datetime.datetime.utcnow)
    entry_gate = Column(String(100), default="Main Campus Gate")
    confidence_avg = Column(Float, default=0.0)
    liveness_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="campus_attendances")
