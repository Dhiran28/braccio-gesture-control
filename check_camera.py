"""Step 1: prove the D435 works on the Pi.

Prints: camera info, USB type, real FPS, distance at the image centre, and how much
of the image has valid depth. Use --show to open a live colour + depth window.

    python check_camera.py           # 10 s test, text only (works over SSH)
    python check_camera.py --show    # live window, press q to quit
"""
import argparse
import time

import numpy as np

from rs_common import start_pipeline, colorize_depth


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true", help="open a live preview window")
    ap.add_argument("--seconds", type=float, default=10)
    args = ap.parse_args()

    rs, pipe, profile, scale = start_pipeline()
    print(f"Depth scale: {scale:.5f} m per unit")
    if args.show:
        import cv2

    n, t0, last_print = 0, time.time(), 0
    valid_hist, centre_hist = [], []
    try:
        while True:
            frames = pipe.wait_for_frames()
            d, c = frames.get_depth_frame(), frames.get_color_frame()
            if not d or not c:
                continue
            n += 1
            depth_m = np.asanyarray(d.get_data()) * scale
            h, w = depth_m.shape
            patch = depth_m[h // 2 - 5:h // 2 + 5, w // 2 - 5:w // 2 + 5]
            patch = patch[patch > 0]
            centre = float(np.median(patch)) if patch.size else 0.0
            valid = float((depth_m > 0).mean())
            valid_hist.append(valid)
            centre_hist.append(centre)

            now = time.time()
            if now - last_print > 1:
                fps = n / (now - t0)
                print(f"FPS {fps:5.1f} | centre distance {centre:5.3f} m | valid depth {valid*100:4.1f}%")
                last_print = now

            if args.show:
                color = np.asanyarray(c.get_data())
                dep = cv2.resize(colorize_depth(depth_m), (color.shape[1], color.shape[0]))
                cv2.circle(dep, (dep.shape[1] // 2, dep.shape[0] // 2), 6, (255, 255, 255), 2)
                cv2.putText(dep, f"{centre:.3f} m", (dep.shape[1] // 2 + 10, dep.shape[0] // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow("D435  colour | depth   (q = quit)", np.hstack([color, dep]))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            elif now - t0 > args.seconds:
                break
    finally:
        pipe.stop()

    fps = n / (time.time() - t0)
    print("\n==== RESULT ====")
    ok = True
    if fps < 20:
        print(f"!! FPS {fps:.1f} is low (expect ~30). Check USB 3 port and power supply.")
        ok = False
    if np.mean(valid_hist) < 0.6:
        print(f"!! Only {np.mean(valid_hist)*100:.0f}% valid depth. Too close (<0.3 m), shiny/black surface, or sunlight?")
        ok = False
    print(f"Average FPS {fps:.1f}, valid depth {np.mean(valid_hist)*100:.0f}%, "
          f"centre distance {np.median(centre_hist):.3f} m")
    print("CAMERA OK" if ok else "CAMERA NEEDS ATTENTION (see warnings above)")


if __name__ == "__main__":
    main()
