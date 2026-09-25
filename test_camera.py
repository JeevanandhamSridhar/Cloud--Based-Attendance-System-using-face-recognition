import time
import cv2


def check_cameras():
    print("=" * 60)
    print("🔍 TESTING CONNECTED WEBCAMS / CAMERAS")
    print("=" * 60)

    working_cams = []

    for index in range(4):
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w, _ = frame.shape
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"[Camera Found] Index {index}: Resolution {w}x{h} @ {fps:.1f} FPS")
                working_cams.append(index)
            cap.release()

    if not working_cams:
        print("[Error] No working cameras detected on indices 0, 1, 2, 3.")
        print("Please check Windows camera privacy permissions (Settings -> Privacy & Security -> Camera).")
        return

    selected_idx = working_cams[0]
    print(f"\nOpening Camera Index {selected_idx} for live test. Press [Q] to close preview...")
    cap = cv2.VideoCapture(selected_idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        curr_time = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(1e-4, curr_time - prev_time))
        prev_time = curr_time

        display = cv2.flip(frame, 1)
        h, w, _ = display.shape

        cv2.putText(
            display,
            f"Camera {selected_idx} Active ({w}x{h}) - FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (0, 255, 120),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            display,
            "Camera Test OK! Press [Q] to close.",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        cv2.imshow("Camera Diagnostic Test - Smart Attendance", display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✅ Camera test complete!")


if __name__ == "__main__":
    check_cameras()
