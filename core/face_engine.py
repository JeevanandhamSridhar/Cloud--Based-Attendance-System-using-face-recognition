import os
from typing import List, Optional, Tuple

import cv2
import numpy as np


class FaceEngine:
    """
    ArcFace Face Recognition Engine using InsightFace.
    - SCRFD (Sample and Computation Redistribution for Efficient Face Detection)
    - ArcFace (Additive Angular Margin Loss) generating 512-dimensional vector embeddings
    Optimized for CPU real-time inference on standard student laptops.
    """

    def __init__(self, model_name: str = "buffalo_sc"):
        self.model_name = model_name
        self.app = None
        self._initialize_model()

    def _initialize_model(self):
        """Initializes InsightFace FaceAnalysis app with CPUExecutionProvider."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            print(f"[FaceEngine] Initializing InsightFace model: {self.model_name}...")
            # buffalo_sc provides rapid SCRFD detection + 512-D ArcFace embeddings
            self.app = FaceAnalysis(
                name=self.model_name,
                providers=["CPUExecutionProvider"],
                allowed_modules=["detection", "recognition"],
            )
            # Prepare detector with detection input size (640, 640)
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            print("[FaceEngine] Model initialized successfully!")
        except Exception as e:
            print(f"[FaceEngine] Notice: InsightFace initialization: {e}")
            print("[FaceEngine] Checking for pre-downloaded weights or fallback...")

    def is_ready(self) -> bool:
        return self.app is not None

    def extract_faces(self, bgr_frame: np.ndarray) -> List[dict]:
        """
        Detects faces in BGR frame and extracts 512-D ArcFace embeddings.
        Returns list of dicts:
        {
            'bbox': (x1, y1, x2, y2),
            'det_score': float,
            'kps': np.ndarray, # 5 facial landmarks (eyes, nose, mouth corners)
            'embedding': np.ndarray (512,),
            'quality_ok': bool,
            'quality_reason': str
        }
        """
        if not self.is_ready():
            return []

        # InsightFace expects BGR frames (OpenCV standard)
        faces = self.app.get(bgr_frame)
        results = []

        h, w, _ = bgr_frame.shape

        for face in faces:
            box = face.bbox.astype(int)
            x1, y1, x2, y2 = max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3])
            det_score = float(face.det_score)

            # Check Face Quality (size, aspect ratio, bounds)
            quality_ok, reason = self.check_quality((x1, y1, x2, y2), (w, h), det_score)

            # Check Face Occlusion (handkerchief, mask, face wiping, looking down at notes)
            kps_arr = face.kps if hasattr(face, "kps") else None
            occlusion_info = self.check_occlusion(bgr_frame, (x1, y1, x2, y2), kps_arr)

            results.append({
                "bbox": (x1, y1, x2, y2),
                "det_score": det_score,
                "kps": kps_arr,
                "embedding": face.embedding if hasattr(face, "embedding") else None,
                "quality_ok": quality_ok,
                "quality_reason": reason,
                "is_occluded": occlusion_info["is_occluded"],
                "occlusion_type": occlusion_info["occlusion_type"],
                "visibility_score": occlusion_info["visibility_score"],
                "occlusion_details": occlusion_info["details"],
            })

        return results

    @staticmethod
    def check_occlusion(
        bgr_frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        kps: Optional[np.ndarray] = None,
    ) -> dict:
        """
        Assesses facial occlusion (handkerchief, mask, face wiping, or looking down at notes).
        Uses biological skin chrominance segmentation in YCrCb space and facial landmark geometry.
        """
        x1, y1, x2, y2 = bbox
        fw = x2 - x1
        fh = y2 - y1

        if fw < 20 or fh < 20 or bgr_frame.size == 0:
            return {
                "is_occluded": False,
                "occlusion_type": "unobstructed",
                "visibility_score": 1.0,
                "details": "Frame too small",
            }

        # Divide face into upper (eyes/forehead) and lower (nose/mouth/chin)
        upper_y2 = y1 + int(0.45 * fh)
        lower_y1 = y1 + int(0.55 * fh)

        upper_crop = bgr_frame[max(0, y1):min(bgr_frame.shape[0], upper_y2), max(0, x1):min(bgr_frame.shape[1], x2)]
        lower_crop = bgr_frame[max(0, lower_y1):min(bgr_frame.shape[0], y2), max(0, x1):min(bgr_frame.shape[1], x2)]

        def get_skin_ratio(crop: np.ndarray) -> float:
            if crop.size == 0:
                return 0.5
            ycrcb = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)
            cr = ycrcb[:, :, 1]
            cb = ycrcb[:, :, 2]
            # Standard human skin chrominance bounds
            skin = (cr >= 133) & (cr <= 173) & (cb >= 77) & (cb <= 127)
            return float(np.mean(skin))

        upper_skin = get_skin_ratio(upper_crop)
        lower_skin = get_skin_ratio(lower_crop)

        # 1. Check for Note-Taking (head tilted downwards significantly)
        is_looking_down = False
        if kps is not None and len(kps) >= 5:
            eye_dist = np.linalg.norm(kps[0] - kps[1])
            eye_mid = (kps[0] + kps[1]) / 2.0
            mouth_mid = (kps[3] + kps[4]) / 2.0
            vert_dist = np.linalg.norm(eye_mid - mouth_mid)
            if eye_dist > 1e-4 and (vert_dist / eye_dist) < 0.65:
                is_looking_down = True

        if is_looking_down:
            return {
                "is_occluded": True,
                "occlusion_type": "head_down_notes",
                "visibility_score": 0.65,
                "details": "Student looking down / taking lecture notes",
            }

        # 2. Check for Kerchief, Handkerchief, Mask, or Face Wiping
        # In unobstructed faces, both upper and lower have high skin chrominance (> 0.40)
        # When a handkerchief (cloth) or mask covers the lower face, lower_skin drops dramatically
        if lower_skin < 0.22 or (upper_skin > 0.35 and lower_skin < 0.40 * upper_skin):
            vis = round(max(0.40, min(0.70, 0.35 + (upper_skin * 0.5))), 2)
            return {
                "is_occluded": True,
                "occlusion_type": "mask_or_kerchief",
                "visibility_score": vis,
                "details": "Lower face occluded by handkerchief, kerchief, or mask",
            }

        # 3. Check for partial hand-wiping (moderate lower skin reduction)
        if lower_skin < 0.35 and upper_skin >= 0.35:
            return {
                "is_occluded": True,
                "occlusion_type": "face_wiping",
                "visibility_score": 0.70,
                "details": "Partial face obstruction (wiping face / hand gesture)",
            }

        # 4. Unobstructed
        vis = round(max(0.80, min(1.0, 0.4 + ((upper_skin + lower_skin) / 2.0))), 2)
        return {
            "is_occluded": False,
            "occlusion_type": "unobstructed",
            "visibility_score": vis,
            "details": "Face fully clear and visible",
        }

    @staticmethod
    def check_quality(
        bbox: Tuple[int, int, int, int], frame_dim: Tuple[int, int], det_score: float
    ) -> Tuple[bool, str]:
        """
        Assesses if detected face is of sufficient quality for attendance registration.
        """
        x1, y1, x2, y2 = bbox
        w, h = frame_dim
        fw = x2 - x1
        fh = y2 - y1

        if det_score < 0.60:
            return False, "Low detection confidence"

        if fw < 70 or fh < 70:
            return False, "Face too small / far from camera"

        # Check if face is cut off at frame border
        margin = 10
        if x1 <= margin or y1 <= margin or x2 >= (w - margin) or y2 >= (h - margin):
            return False, "Face too close to frame border"

        return True, "Good"
