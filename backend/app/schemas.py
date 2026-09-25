import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------
# AUTH SCHEMAS
# ---------------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str
    role: str = "faculty"  # admin, faculty, student


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


# ---------------------------------------------------------
# STUDENT SCHEMAS
# ---------------------------------------------------------
class StudentCreate(BaseModel):
    student_id: str
    name: str
    department: str = "Computer Science"
    year: int = 3
    section: str = "A"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class StudentResponse(BaseModel):
    id: str
    student_id: str
    name: str
    department: str
    year: int
    section: str
    email: Optional[str] = None
    has_face_registered: bool = False
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class EnrollFaceRequest(BaseModel):
    # Either provide a pre-extracted 512-D vector, single image, or multi-shot list of images
    embedding: Optional[List[float]] = None
    image_base64: Optional[str] = None
    images_base64: Optional[List[str]] = None


# ---------------------------------------------------------
# SUBJECT & SESSION SCHEMAS
# ---------------------------------------------------------
class SubjectCreate(BaseModel):
    code: str
    name: str
    department: str = "Computer Science"


class SubjectResponse(BaseModel):
    id: str
    code: str
    name: str
    department: str
    faculty_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SessionCreate(BaseModel):
    subject_id: str
    room: str = "Lab-01"
    start_time: datetime.datetime
    end_time: datetime.datetime
    checkpoint_interval_mins: int = 5
    min_presence_percentage: float = 75.0


class SessionResponse(BaseModel):
    id: str
    subject_id: str
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    room: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    status: str
    checkpoint_interval_mins: int
    min_presence_percentage: float
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# ATTENDANCE & INFERENCE SCHEMAS
# ---------------------------------------------------------
class ScanFrameRequest(BaseModel):
    session_id: str
    image_base64: str
    client_is_live: bool = True
    ear_value: Optional[float] = None
    camera_id: str = "WEBCAM-01"


class DetectedStudentMatch(BaseModel):
    student_id: Optional[str] = None
    student_code: Optional[str] = None
    student_name: Optional[str] = None
    confidence: float
    is_live: bool
    liveness_status: str
    ear: Optional[float] = None
    bbox: List[int]
    status: str  # present, present_occluded, flagged, unknown, spoof_rejected
    is_occluded: bool = False
    occlusion_type: str = "unobstructed"
    visibility_score: float = 1.0


class ScanResultResponse(BaseModel):
    session_id: str
    faces_detected: int
    students_recognized: int
    matches: List[DetectedStudentMatch]


class AttendanceRecordResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    student_code: str
    student_name: str
    department: str
    status: str
    presence_score: float
    confidence_avg: float
    checkpoints_detected: int
    total_checkpoints: int
    face_visibility_score: float = 100.0
    occlusion_count: int = 0
    first_seen: Optional[datetime.datetime] = None
    last_seen: Optional[datetime.datetime] = None
    verified_by_faculty: bool = False

    model_config = ConfigDict(from_attributes=True)


class VerifyAttendanceRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


# ---------------------------------------------------------
# ANALYTICS SCHEMAS
# ---------------------------------------------------------
class LowAttendanceAlert(BaseModel):
    student_id: str
    student_code: str
    name: str
    department: str
    attendance_pct: float


class DashboardSummaryResponse(BaseModel):
    total_enrolled_students: int
    active_sessions_count: int
    today_total_attendances: int
    today_present_count: int
    today_partial_count: int
    today_absent_count: int
    average_presence_percentage: float
    low_attendance_students: List[LowAttendanceAlert]
    today_campus_entry_count: int = 0
    bunking_flagged_count: int = 0


# ---------------------------------------------------------
# CAMPUS & TRUANCY AUDIT SCHEMAS
# ---------------------------------------------------------
class DailyCampusAttendanceResponse(BaseModel):
    id: str
    student_id: str
    student_name: str
    student_code: str
    department: str
    date: datetime.datetime
    status: str
    first_entry_time: Optional[datetime.datetime] = None
    last_seen_time: Optional[datetime.datetime] = None
    entry_gate: str
    confidence_avg: float
    liveness_verified: bool

    model_config = ConfigDict(from_attributes=True)


class BunkingAuditItem(BaseModel):
    student_id: str
    student_code: str
    student_name: str
    department: str
    campus_status: str  # "present_on_campus" | "absent_from_campus"
    campus_entry_time: Optional[datetime.datetime] = None
    class_status: str  # "present" | "partial" | "absent"
    class_presence_score: float
    classification: str  # "ATTENDING_CLASS", "BUNKING_CLASS", "FULL_DAY_ABSENT"
    discrepancy_badge: str
