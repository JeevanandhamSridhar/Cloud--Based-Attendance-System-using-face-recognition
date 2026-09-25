import os
import sys
import time

import cv2
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.face_engine import FaceEngine
from core.liveness import LivenessDetector
from core.matcher import FaceMatcher


def draw_styled_box(img, pt1, pt2, color, thickness=2, r=15, d=20):
    """Draws rounded-corner bounding box with modern aesthetics."""
    x1, y1 = pt1
    x2, y2 = pt2

    # Top-left corner
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)

    # Top-right corner
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)

    # Bottom-left corner
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)

    # Bottom-right corner
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)


def main():
    print("=" * 60)
    print("🎥 SMART ATTENDANCE - REAL-TIME FACE RECOGNITION & LIVENESS")
    print("=" * 60)

    # 1. Initialize Face Engine
    print("[AI Engine] Loading ArcFace & SCRFD face detector...")
    engine = FaceEngine()

    # 2. Initialize Matcher & Database
    matcher = FaceMatcher(threshold=0.48)
    student_count = len(matcher.students)
    print(f"[Matcher] Loaded {student_count} registered students from 'data/embeddings.json'")

    if student_count == 0:
        print("\n⚠️ [WARNING] No registered students found in database!")
        print("Please run `python register.py` first to enroll your face.")
        proceed = input("Do you still want to run camera test? [y/N]: ").strip().lower()
        if proceed != "y":
            return

    # 3. Initialize Liveness Detector
    print("[Liveness] Initializing MediaPipe FaceMesh & EAR anti-spoofing...")
    liveness_detector = LivenessDetector()

    # 4. Open Webcam
    print("[Camera] Starting webcam (Index 0)...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam index 0. Try running test_camera.py.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("\nControls:")
    print(" - Press [Q] to Exit")
    print(" - Press [R] to Reload registered student embeddings")
    print(" - Press [S] to Save a screenshot\n")

    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Camera] Failed to grab frame.")
            break

        # Horizontal mirror flip
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        display = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # FPS calculation
        curr_time = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-4, curr_time - prev_time))
        prev_time = curr_time

        # 1. Detect faces & extract 512-D ArcFace embeddings
        detected_faces = engine.extract_faces(frame)

        # 2. Run liveness check
        face_boxes = [f["bbox"] for f in detected_faces]
        liveness_results = liveness_detector.analyze_frame(rgb_frame, face_boxes=face_boxes)

        # Map liveness results by bounding box proximity
        def get_liveness_for_box(target_box):
            tx1, ty1, tx2, ty2 = target_box
            tcx, tcy = (tx1 + tx2) / 2.0, (ty1 + ty2) / 2.0
            best = None
            min_d = float("inf")
            for lr in liveness_results:
                lx1, ly1, lx2, ly2 = lr["box"]
                lcx, lcy = (lx1 + lx2) / 2.0, (ly1 + ly2) / 2.0
                d = np.hypot(tcx - lcx, tcy - lcy)
                if d < min_d and d < 120:
                    min_d = d
                    best = lr
            return best

        # 3. Process each face
        recognized_count = 0
        for face in detected_faces:
            x1, y1, x2, y2 = face["bbox"]
            emb = face["embedding"]
            det_score = face["det_score"]

            # Match against database
            student_id, student_name, similarity, is_match = matcher.match(emb)
            confidence_pct = round(similarity * 100, 1)

            # Liveness status
            live_info = get_liveness_for_box((x1, y1, x2, y2))
            is_live = live_info["is_live"] if live_info else False
            status_text = live_info["status"] if live_info else "Checking Liveness..."
            ear_val = live_info["ear"] if live_info else 0.0
            is_spoof = "SPOOF" in status_text

            # Visual styling decisions
            if is_match and is_live:
                # Verified Present!
                box_color = (0, 230, 100)  # Bright Green
                primary_label = f"{student_name} ({confidence_pct}%)"
                sub_label = f"ID: {student_id} | LIVE: PASS (EAR {ear_val})"
                recognized_count += 1
            elif is_match and is_spoof:
                # Presentation Attack Detected!
                box_color = (0, 0, 240)  # Crimson Red
                primary_label = f"{student_name} - SPOOF DETECTED"
                sub_label = "REJECTED: Static Photo / Screen"
            elif is_match:
                # Recognized, waiting for blink verification
                box_color = (0, 215, 255)  # Cyan / Yellow
                primary_label = f"{student_name} ({confidence_pct}%)"
                sub_label = f"ID: {student_id} | Blink eyes to verify..."
            else:
                # Unknown Person
                box_color = (150, 150, 150)  # Neutral Gray / Orange
                primary_label = "Unknown Face"
                sub_label = f"Similarity: {confidence_pct}% (< {int(matcher.threshold*100)}%)"

            # Draw rounded box
            draw_styled_box(display, (x1, y1), (x2, y2), box_color, thickness=2)

            # Draw label badges with semi-transparent background
            label_w = max(len(primary_label), len(sub_label)) * 11 + 20
            label_y1 = max(0, y1 - 48)
            label_y2 = y1

            cv2.rectangle(
                display,
                (x1, label_y1),
                (x1 + label_w, label_y2),
                box_color,
                -1,
            )
            # Primary text
            cv2.putText(
                display,
                primary_label,
                (x1 + 8, label_y1 + 20),
                cv2.FONT_HERSHEY_DUPLEX,
                0.55,
                (0, 0, 0) if box_color != (0, 0, 240) else (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
            # Sub text
            cv2.putText(
                display,
                sub_label,
                (x1 + 8, label_y1 + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0) if box_color != (0, 0, 240) else (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # Top HUD Dashboard Bar
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, 55), (20, 20, 25), -1)
        cv2.addWeighted(overlay, 0.8, display, 0.2, 0, display)

        cv2.putText(
            display,
            f"SMART ATTENDANCE MONITOR | FPS: {fps:.1f}",
            (20, 24),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            f"Enrolled: {student_count} | In Frame: {len(detected_faces)} | Verified Live: {recognized_count} | [Q] Exit",
            (20, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 220, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.imshow("Smart Attendance - Live Recognition & Liveness Monitor", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            cnt = matcher.load_database()
            student_count = cnt
            print(f"[Matcher] Database reloaded: {cnt} students found.")
        elif key == ord("s"):
            fname = f"snapshot_{int(time.time())}.jpg"
            cv2.imwrite(fname, display)
            print(f"[Camera] Saved snapshot to {fname}")

    cap.release()
    cv2.destroyAllWindows()
    print("[Shutdown] Recognition monitor stopped.")


if __name__ == "__main__":
    main()
