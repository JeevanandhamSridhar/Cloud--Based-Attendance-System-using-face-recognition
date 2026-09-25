import os
import sys
import time

import cv2
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.face_engine import FaceEngine
from core.matcher import FaceMatcher


def draw_styled_box(img, pt1, pt2, color, thickness=2, r=15, d=20):
    """Draws a modern rounded-corner bounding box."""
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
    print("🎓 SMART ATTENDANCE - STUDENT FACE ENROLLMENT")
    print("=" * 60)

    student_id = input("Enter Student ID (e.g., 23CS001): ").strip()
    if not student_id:
        print("[Error] Student ID cannot be empty.")
        return

    name = input("Enter Student Name (e.g., Alex Johnson): ").strip()
    if not name:
        print("[Error] Student Name cannot be empty.")
        return

    department = input("Enter Department [Default: Computer Science]: ").strip()
    if not department:
        department = "Computer Science"

    print("\n[AI Engine] Initializing ArcFace SCRFD embedding model...")
    engine = FaceEngine()
    matcher = FaceMatcher()

    print("[Camera] Connecting to webcam...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam index 0. Try running test_camera.py.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    samples_needed = 5
    collected_embeddings = []
    best_face_crop = None

    print("\nInstructions:")
    print(" - Look straight at the camera with clear lighting.")
    print(" - Slightly adjust head angle between shots (neutral, slight smile, slight left/right).")
    print(" - Press [SPACE] to capture each sample, or [Q] to quit.")

    cooldown = 0

    while len(collected_embeddings) < samples_needed:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip horizontally for natural mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        display = frame.copy()

        # Semi-transparent header banner
        overlay = display.copy()
        cv2.rectangle(overlay, (0, 0), (w, 80), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.75, display, 0.25, 0, display)

        # Header text
        cv2.putText(
            display,
            f"REGISTER: {name} ({student_id}) - {department}",
            (25, 32),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            f"Captured: {len(collected_embeddings)} / {samples_needed} Samples | Press [SPACE] to capture, [Q] to Cancel",
            (25, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 220, 255),
            1,
            cv2.LINE_AA,
        )

        # Detect face & quality
        faces = engine.extract_faces(frame)
        current_valid_face = None

        if len(faces) == 0:
            cv2.putText(
                display,
                "No face detected. Position yourself in front of the camera.",
                (w // 2 - 250, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )
        elif len(faces) > 1:
            cv2.putText(
                display,
                "Multiple faces detected! Please ensure only ONE student is in frame.",
                (w // 2 - 300, h - 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 165, 255),
                2,
                cv2.LINE_AA,
            )
        else:
            face = faces[0]
            x1, y1, x2, y2 = face["bbox"]
            quality_ok = face["quality_ok"]
            reason = face["quality_reason"]

            if quality_ok:
                color = (0, 255, 120)  # Bright green
                status_msg = "Ready for capture! Press [SPACE]"
                current_valid_face = face
            else:
                color = (0, 140, 255)  # Orange
                status_msg = f"Adjust position: {reason}"

            draw_styled_box(display, (x1, y1), (x2, y2), color, thickness=2)
            cv2.putText(
                display,
                status_msg,
                (x1, max(30, y1 - 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
                cv2.LINE_AA,
            )

        # Progress bar at bottom
        bar_w = 400
        bar_h = 16
        bx = (w - bar_w) // 2
        by = h - 60
        progress = len(collected_embeddings) / float(samples_needed)
        cv2.rectangle(display, (bx, by), (bx + bar_w, by + bar_h), (50, 50, 50), -1)
        cv2.rectangle(
            display,
            (bx, by),
            (bx + int(bar_w * progress), by + bar_h),
            (0, 220, 100),
            -1,
        )
        cv2.rectangle(display, (bx, by), (bx + bar_w, by + bar_h), (200, 200, 200), 1)

        cv2.imshow("Student Face Registration - Smart Attendance", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("\n[Cancel] Registration cancelled by user.")
            cap.release()
            cv2.destroyAllWindows()
            return

        if key == 32:  # SPACE bar
            if current_valid_face is not None and current_valid_face["embedding"] is not None:
                emb = current_valid_face["embedding"]
                collected_embeddings.append(emb)
                print(f" -> Sample {len(collected_embeddings)}/{samples_needed} recorded!")

                # Save best cropped profile image
                x1, y1, x2, y2 = current_valid_face["bbox"]
                best_face_crop = frame[y1:y2, x1:x2].copy()

                # Visual capture flash
                flash = np.full_like(frame, 255)
                cv2.imshow("Student Face Registration - Smart Attendance", flash)
                cv2.waitKey(80)
            else:
                print(" -> Please ensure face is centered and green box is visible before capturing.")

    cap.release()
    cv2.destroyAllWindows()

    print("\n[Processing] Aggregating 5-shot ArcFace embeddings...")
    # Compute normalized mean embedding across 5 samples
    mean_embedding = np.mean(collected_embeddings, axis=0)
    norm = np.linalg.norm(mean_embedding)
    if norm > 1e-6:
        mean_embedding = mean_embedding / norm

    # Save to embeddings database
    matcher.save_student(
        student_id=student_id,
        name=name,
        department=department,
        embedding=mean_embedding,
    )

    # Save face thumbnail if present
    if best_face_crop is not None and best_face_crop.size > 0:
        os.makedirs("data/faces", exist_ok=True)
        crop_path = os.path.join("data", "faces", f"{student_id}.jpg")
        cv2.imwrite(crop_path, best_face_crop)

    print("=" * 60)
    print(f" SUCCESS: Student '{name}' ({student_id}) enrolled successfully!")
    print(f" -> 512-Dimensional ArcFace vector saved to 'data/embeddings.json'")
    print(f" -> Total registered students in system: {len(matcher.students)}")
    print("=" * 60)
    print("\nYou can now run `python recognize.py` to test live recognition and liveness!")


if __name__ == "__main__":
    main()
