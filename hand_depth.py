"""Step 2: hand tracking + gestures with REAL 3D position from depth.

MediaPipe finds 21 hand points in the colour image. For a few key points we look up the
depth (no full-frame alignment, so it stays fast on a Pi), and turn them into real
X/Y/Z in metres. Gesture is decided from 3D distances, so it works at any distance.

Only hands inside the interaction zone (0.3 - 1.5 m by default) are used, so people
walking behind the visitor are ignored.

    python hand_depth.py            # text output
    python hand_depth.py --show     # live window with skeleton + gesture
"""
import argparse
import os
import time

import numpy as np

# MediaPipe landmark ids
WRIST, THUMB_TIP, INDEX_MCP, INDEX_TIP, MIDDLE_MCP, MIDDLE_TIP, RING_TIP, PINKY_MCP, PINKY_TIP = 0, 4, 5, 8, 9, 12, 16, 17, 20
INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP = 6, 10, 14, 18
KEY_POINTS = [WRIST, THUMB_TIP, INDEX_MCP, INDEX_PIP, INDEX_TIP, MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP,
              RING_PIP, RING_TIP, PINKY_MCP, PINKY_PIP, PINKY_TIP]
HAND_CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
                    (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17)]


def classify_gesture(p):
    """p: dict landmark_id -> np.array([x,y,z]) in metres. Returns 'pinch' | 'fist' | 'open' | 'point' | 'unknown'."""
    need = [WRIST, THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP, INDEX_MCP, PINKY_MCP,
            INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]
    if any(k not in p for k in need):
        return "unknown"
    palm = np.linalg.norm(p[INDEX_MCP] - p[PINKY_MCP])          # palm width, ~7-9 cm
    if palm < 0.02:
        return "unknown"

    def extended(tip, pip):
        # finger is straight if its tip is further from the wrist than its middle joint
        return np.linalg.norm(p[tip] - p[WRIST]) > np.linalg.norm(p[pip] - p[WRIST]) * 1.1

    fingers = [extended(INDEX_TIP, INDEX_PIP), extended(MIDDLE_TIP, MIDDLE_PIP),
               extended(RING_TIP, RING_PIP), extended(PINKY_TIP, PINKY_PIP)]
    pinch_d = np.linalg.norm(p[THUMB_TIP] - p[INDEX_TIP])

    if pinch_d < 0.35 * palm:
        return "pinch"
    if not any(fingers):
        return "fist"
    if all(fingers):
        return "open"
    if fingers[0] and not any(fingers[1:]):
        return "point"
    return "unknown"


def depth_at_color_pixel(rs, depth_frame, depth_img, scale, d_intr, c_intr, d2c, c2d, u, v, win=3):
    """Find the depth (m) for a colour-image pixel without aligning the whole frame."""
    dpx = rs.rs2_project_color_pixel_to_depth_pixel(
        depth_frame.get_data(), scale, 0.1, 3.0, d_intr, c_intr, d2c, c2d, [float(u), float(v)])
    x, y = int(round(dpx[0])), int(round(dpx[1]))
    h, w = depth_img.shape
    if not (0 <= x < w and 0 <= y < h):
        return 0.0
    patch = depth_img[max(0, y - win):y + win + 1, max(0, x - win):x + win + 1].astype(np.float32) * scale
    patch = patch[patch > 0]
    return float(np.median(patch)) if patch.size else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--zmin", type=float, default=0.3, help="interaction zone near limit (m)")
    ap.add_argument("--zmax", type=float, default=1.5, help="interaction zone far limit (m)")
    ap.add_argument("--model", default=os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task"))
    args = ap.parse_args()

    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    from rs_common import start_pipeline

    if not os.path.exists(args.model):
        raise SystemExit(f"Hand model not found at {args.model}. Run setup_pi.sh step 6.")

    landmarker = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=args.model),
        running_mode=vision.RunningMode.VIDEO, num_hands=1,
        min_hand_detection_confidence=0.6, min_tracking_confidence=0.5))

    rs, pipe, profile, scale = start_pipeline()
    d_prof = profile.get_stream(rs.stream.depth).as_video_stream_profile()
    c_prof = profile.get_stream(rs.stream.color).as_video_stream_profile()
    d_intr, c_intr = d_prof.get_intrinsics(), c_prof.get_intrinsics()
    d2c, c2d = d_prof.get_extrinsics_to(c_prof), c_prof.get_extrinsics_to(d_prof)

    t0 = time.time()
    n, last_print, smooth = 0, 0, None
    try:
        while True:
            frames = pipe.wait_for_frames()
            df, cf = frames.get_depth_frame(), frames.get_color_frame()
            if not df or not cf:
                continue
            n += 1
            color = np.asanyarray(cf.get_data())
            depth_img = np.asanyarray(df.get_data())
            rgb = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
            res = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb),
                                              int((time.time() - t0) * 1000))

            status = "no hand"
            if res.hand_landmarks:
                lms = res.hand_landmarks[0]
                px = {i: (lm.x * c_intr.width, lm.y * c_intr.height) for i, lm in enumerate(lms)}
                pts = {}
                for i in KEY_POINTS:
                    u, v = px[i]
                    z = depth_at_color_pixel(rs, df, depth_img, scale, d_intr, c_intr, d2c, c2d, u, v)
                    if z > 0:
                        pts[i] = np.array(rs.rs2_deproject_pixel_to_point(c_intr, [u, v], z))
                if WRIST in pts and args.zmin <= pts[WRIST][2] <= args.zmax:
                    g = classify_gesture(pts)
                    w = pts[WRIST]
                    smooth = w if smooth is None else 0.7 * smooth + 0.3 * w   # simple smoothing
                    status = (f"{g:7s} | wrist X {smooth[0]:+.3f}  Y {smooth[1]:+.3f}  Z {smooth[2]:.3f} m")
                elif WRIST in pts:
                    status = f"hand outside zone (Z {pts[WRIST][2]:.2f} m)"
                else:
                    status = "hand seen, no depth at wrist"

                if args.show:
                    for a, b in HAND_CONNECTIONS:
                        cv2.line(color, tuple(map(int, px[a])), tuple(map(int, px[b])), (0, 255, 0), 2)

            now = time.time()
            if now - last_print > 0.25:
                print(f"[{n / (now - t0):4.1f} fps] {status}")
                last_print = now
            if args.show:
                cv2.putText(color, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.imshow("Hand + depth  (q = quit)", color)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        pipe.stop()


if __name__ == "__main__":
    main()
