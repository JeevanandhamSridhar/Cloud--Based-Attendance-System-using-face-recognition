import os
import shutil
import tempfile
import numpy as np
import pytest

from core.face_engine import FaceEngine
from core.matcher import FaceMatcher
from core.liveness import LivenessDetector


def test_face_engine_initialization():
    """Verify ArcFace InsightFace SCRFD model loads and is ready."""
    engine = FaceEngine()
    assert engine.is_ready() is True


def test_matcher_cosine_similarity():
    """Verify normalized dot-product cosine similarity math."""
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_embeddings.json")

    try:
        matcher = FaceMatcher(db_path=temp_db, threshold=0.50)

        # Vector A: 512-D random unit vector
        np.random.seed(42)
        vec_a = np.random.randn(512).astype(np.float32)
        vec_a = vec_a / np.linalg.norm(vec_a)

        # Save student
        matcher.save_student(
            student_id="23CS001",
            name="Jeeva",
            department="Computer Science",
            embedding=vec_a,
        )

        # 1. Matching exact same embedding should give similarity ~ 1.0
        sid, name, sim, is_match = matcher.match(vec_a)
        assert sid == "23CS001"
        assert name == "Jeeva"
        assert pytest.approx(sim, abs=1e-4) == 1.0
        assert is_match is True

        # 2. Matching with random independent vector should fail match threshold
        vec_b = np.random.randn(512).astype(np.float32)
        vec_b = vec_b / np.linalg.norm(vec_b)
        _, _, sim_b, is_match_b = matcher.match(vec_b)
        assert sim_b < 0.50
        assert is_match_b is False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_liveness_ear_calculation():
    """Verify Soukupová & Čech Eye Aspect Ratio (EAR) calculations."""
    detector = LivenessDetector()

    # Synthetic eye landmarks: [p1, p2, p3, p4, p5, p6]
    # Open eye: horizontal width = 20, vertical openings = 6
    open_eye = [
        (10.0, 30.0),  # p1: outer corner
        (16.0, 24.0),  # p2: upper top
        (24.0, 24.0),  # p3: upper bottom
        (30.0, 30.0),  # p4: inner corner
        (24.0, 36.0),  # p5: lower bottom
        (16.0, 36.0),  # p6: lower top
    ]
    # Indices [0, 1, 2, 3, 4, 5]
    ear_open = detector.calculate_ear(open_eye, [0, 1, 2, 3, 4, 5])

    # Closed eye: vertical distance drops near zero
    closed_eye = [
        (10.0, 30.0),  # p1
        (16.0, 29.5),  # p2
        (24.0, 29.5),  # p3
        (30.0, 30.0),  # p4
        (24.0, 30.5),  # p5
        (16.0, 30.5),  # p6
    ]
    ear_closed = detector.calculate_ear(closed_eye, [0, 1, 2, 3, 4, 5])

    assert ear_open > 0.25
    assert ear_closed < 0.10
    assert ear_open > (ear_closed * 2.5)


def test_face_occlusion_and_handkerchief_detection():
    """Verify handkerchief/mask occlusion detection on lower face."""
    engine = FaceEngine()

    # 1. Unobstructed face mock (skin tone BGR: 120, 150, 180 -> YCrCb skin region)
    clear_face = np.full((120, 100, 3), [120, 150, 180], dtype=np.uint8)
    res_clear = engine.check_occlusion(clear_face, (0, 0, 100, 120))
    assert res_clear["is_occluded"] is False
    assert res_clear["occlusion_type"] == "unobstructed"
    assert res_clear["visibility_score"] >= 0.80

    # 2. Handkerchief/Mask covered face (lower 50% covered by white cloth)
    masked_face = clear_face.copy()
    masked_face[60:120, :] = [255, 255, 255]
    res_masked = engine.check_occlusion(masked_face, (0, 0, 100, 120))
    assert res_masked["is_occluded"] is True
    assert res_masked["occlusion_type"] == "mask_or_kerchief"
    assert res_masked["visibility_score"] < 0.75
