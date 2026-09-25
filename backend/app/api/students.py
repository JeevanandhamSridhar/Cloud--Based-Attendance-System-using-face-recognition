import base64
import json
import numpy as np
import cv2
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import FaceEmbedding, Student, User
from backend.app.schemas import EnrollFaceRequest, StudentCreate, StudentResponse
from backend.app.security import require_faculty_or_admin
from core.face_engine import FaceEngine
from core.matcher import FaceMatcher

router = APIRouter(prefix="/students", tags=["Student Management"])

# Initialize FaceEngine lazily for server-side face vector extraction
face_engine = None


def get_face_engine():
    global face_engine
    if face_engine is None:
        face_engine = FaceEngine()
    return face_engine


@router.get("", response_model=List[StudentResponse])
def list_students(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Lists all enrolled students with their face registration status."""
    students = db.query(Student).offset(skip).limit(limit).all()
    results = []
    for s in students:
        has_face = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == s.id).first() is not None
        results.append(
            StudentResponse(
                id=s.id,
                student_id=s.student_id,
                name=s.name,
                department=s.department,
                year=s.year,
                section=s.section,
                email=s.email,
                has_face_registered=has_face,
                created_at=s.created_at,
            )
        )
    return results


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """Enrolls a new student in the database registry."""
    existing = db.query(Student).filter(Student.student_id == student_in.student_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with ID '{student_in.student_id}' is already registered.",
        )

    student = Student(
        student_id=student_in.student_id,
        name=student_in.name,
        department=student_in.department,
        year=student_in.year,
        section=student_in.section,
        email=student_in.email,
        phone=student_in.phone,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        year=student.year,
        section=student.section,
        email=student.email,
        has_face_registered=False,
        created_at=student.created_at,
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    student = db.query(Student).filter(
        (Student.id == student_id) | (Student.student_id == student_id)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    has_face = db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student.id).first() is not None
    return StudentResponse(
        id=student.id,
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        year=student.year,
        section=student.section,
        email=student.email,
        has_face_registered=has_face,
        created_at=student.created_at,
    )


@router.post("/{student_id}/enroll-face")
def enroll_student_face(
    student_id: str,
    payload: EnrollFaceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    """
    Stores the 512-D ArcFace vector embedding for a student.
    Strictly follows Privacy by Design: raw photos are discarded, only vector embeddings are stored.
    """
    student = db.query(Student).filter(
        (Student.id == student_id) | (Student.student_id == student_id)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    embedding_vector = None
    engine = get_face_engine()

    if payload.embedding and len(payload.embedding) == 512:
        embedding_vector = np.array(payload.embedding, dtype=np.float32)
    elif payload.images_base64 and len(payload.images_base64) > 0:
        # 5-Shot Multi-Angle Enrollment (averages embeddings for maximum robustness)
        collected_vectors = []
        for img_b64 in payload.images_base64:
            try:
                raw_data = img_b64
                if "," in raw_data:
                    raw_data = raw_data.split(",")[1]
                img_bytes = base64.b64decode(raw_data)
                nparr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                faces = engine.extract_faces(frame)
                if faces and faces[0]["embedding"] is not None:
                    collected_vectors.append(faces[0]["embedding"])
            except Exception:
                continue

        if not collected_vectors:
            raise HTTPException(status_code=400, detail="No face detected in any of the captured images. Please retake.")

        # Compute normalized mean ArcFace embedding across all captured angles
        mean_vec = np.mean(collected_vectors, axis=0)
        norm = np.linalg.norm(mean_vec)
        embedding_vector = mean_vec / norm if norm > 1e-6 else mean_vec
    elif payload.image_base64:
        # Single frame enrollment
        try:
            raw_data = payload.image_base64
            if "," in raw_data:
                raw_data = raw_data.split(",")[1]
            img_bytes = base64.b64decode(raw_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            faces = engine.extract_faces(frame)
            if not faces:
                raise HTTPException(status_code=400, detail="No face detected in the provided image.")
            if len(faces) > 1:
                raise HTTPException(status_code=400, detail="Multiple faces detected. Frame must contain exactly one face.")

            embedding_vector = faces[0]["embedding"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process face frame: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Must provide either a 512-D embedding, image_base64, or images_base64 list.")

    # L2-normalize vector
    norm = np.linalg.norm(embedding_vector)
    if norm > 1e-6:
        embedding_vector = embedding_vector / norm

    # Remove previous embedding if updating
    db.query(FaceEmbedding).filter(FaceEmbedding.student_id == student.id).delete()

    # Save to database
    face_record = FaceEmbedding(
        student_id=student.id,
        embedding_json=json.dumps(embedding_vector.tolist()),
        model_version="ArcFace_SCRFD_buffalo_sc_512",
        is_primary=True,
    )
    db.add(face_record)
    db.commit()

    # Also sync to local FaceMatcher for zero-latency local fallback
    matcher = FaceMatcher()
    matcher.save_student(
        student_id=student.student_id,
        name=student.name,
        department=student.department,
        embedding=embedding_vector,
    )

    return {
        "success": True,
        "message": f"ArcFace 512-D embedding enrolled successfully for {student.name} ({student.student_id}).",
        "student_id": student.student_id,
        "embedding_dimensions": 512,
    }


@router.delete("/{student_id}")
def delete_student(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_faculty_or_admin),
):
    student = db.query(Student).filter(
        (Student.id == student_id) | (Student.student_id == student_id)
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return {"success": True, "message": f"Student '{student.name}' removed successfully."}
