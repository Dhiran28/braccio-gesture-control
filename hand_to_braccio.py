"""Step 4: hand gestures + 3D hand position -> Braccio joint angles -> UNO R4 over UDP.

Talks to your existing braccio_udp.ino (UDP port 5005, packet "base,shoulder,elbow,wristUpDown,wristTwist,gripper").

Control style (CONTROL_MODE): "absolute" (default) - the gripper goes to the spot matching where your hand
is in front of the camera. Stand facing the camera ~60 cm away, camera at chest height, arm beside the camera.

What moves what
  hand left/right (X)       -> M1 base turn
  hand up/down (Y)          -> gripper height   } solved with inverse kinematics
  hand nearer/further (Z)   -> gripper reach    } into M2 shoulder, M3 elbow, M4 wrist
  palm roll (turn a key)    -> M5 wrist twist
  gesture                   -> M6 gripper + safety

Gestures
  open palm = arm follows your hand, gripper OPEN
  fist      = arm follows your hand, gripper CLOSED (grab and carry)
  hand out of view = arm holds still; bring your hand back anywhere and it carries on from there
  no hand for 2 s = arm goes to HOME pose

Keys in the --show window: q = quit (arm goes HOME), space = pause/resume (arm holds still)

SAFE ORDER OF USE
  1) python hand_to_braccio.py --show                  # SIMULATION: nothing is sent to the arm
  2) python hand_to_braccio.py --check --show --arm-ip <IP>   # 3 slow test poses; compare the real arm with the drawing
  3) python hand_to_braccio.py --show --arm-ip <IP>     # LIVE. Keep a hand on the arm's 5V plug.
"""
import argparse
import math
import os
import socket
import time

import numpy as np

# ===================== SETTINGS YOU MAY TUNE =====================
PORT = 5005

# Braccio link lengths in metres (base->shoulder, shoulder->elbow, elbow->wrist, wrist->gripper tip)
L0, L1, L2, L3 = 0.0715, 0.125, 0.125, 0.192

# Servo limits from braccio_udp.ino (base, shoulder, elbow, wristUpDown, wristTwist, gripper)
LO = [0, 15, 0, 0, 0, 10]
HI = [180, 165, 180, 180, 180, 73]
GRIP_OPEN, GRIP_CLOSED = 20, 70          # 73 = fully closed; 70 grips without stalling the servo hard

# Direction signs + offsets: fix these if --check shows a joint going the wrong way
SHOULDER_SIGN, ELBOW_SIGN, WRIST_SIGN = +1, +1, +1
TWIST_ENABLED = False                     # wrist twist from turning your hand. Off = wrist twist stays at 90 (most stable)
TWIST_DEADBAND = 15                       # degrees of hand turn ignored around the centre (stops twitching)
TWIST_SIGN = +1                           # flip to -1 if the wrist twists the opposite way to your hand
SHOULDER_OFFSET = 0                       # degrees added to the servo value; set by calibrate.py
ELBOW_OFFSET = 0
WRIST_OFFSET = 0                          # your candle test showed the wrist ~10-15 deg off: put the correction here

HOME = [90, 90, 90, 90, 90, GRIP_OPEN]    # candle pose, gripper open

# calibration.json (written by calibrate.py) overrides the offsets/signs above
CAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")
try:
    import json as _json
    with open(CAL_FILE) as _f:
        _cal = _json.load(_f)
    SHOULDER_OFFSET = _cal.get("shoulder_offset", SHOULDER_OFFSET)
    ELBOW_OFFSET = _cal.get("elbow_offset", ELBOW_OFFSET)
    WRIST_OFFSET = _cal.get("wrist_offset", WRIST_OFFSET)
    SHOULDER_SIGN = _cal.get("shoulder_sign", SHOULDER_SIGN)
    ELBOW_SIGN = _cal.get("elbow_sign", ELBOW_SIGN)
    WRIST_SIGN = _cal.get("wrist_sign", WRIST_SIGN)
    L0 = _cal.get("base_mm", L0 * 1000) / 1000
    HOME = [90, 90 + SHOULDER_OFFSET, 90 + ELBOW_OFFSET, 90 + WRIST_OFFSET, 90, GRIP_OPEN]
except (OSError, ValueError):
    pass

# Hand box in front of the camera (metres, camera frame: x right, y down, z away from camera)
HAND_X = (-0.20, 0.20)
HAND_Y = (-0.18, 0.18)
HAND_Z = (0.40, 0.80)
ZONE = (0.30, 1.20)                       # hand is used only between 30 cm and 1.2 m from the camera (best: 50-90 cm)
MIRROR_X = True                           # visitor faces the camera: their right appears on the image left

# Where that box maps to on the robot side
BASE_RANGE = (40, 140)                    # degrees of base turn used (90 = straight ahead)
REACH = (0.20, 0.32)                      # gripper tip horizontal distance from base axis (m) - Braccio can't pick closer than ~18 cm with the gripper down
HEIGHT = (0.03, 0.22)                     # gripper tip height above table (m) - never lower than 3 cm
NEAR_MEANS_FAR = True                     # hand closer to camera -> arm reaches further (toward the visitor)

UPPER_ARM_MAX_DEG = 92                    # upper arm stays upright or leans FORWARD, like a person reaching

# --- control mode
#   "absolute": the gripper always goes to the spot that matches where your hand is inside the box
#               (camera centre = arm facing forward, mid height). Hand and arm can never drift apart.
#   "relative": like a mouse - the gripper moves by how much your hand moves, from wherever it is.
CONTROL_MODE = "absolute"

# --- gripper angle: points straight down near the table, tilts forward when higher up
APPROACH_LOW = -90                        # deg, at the lowest height (-90 = straight down, best for picking)
APPROACH_HIGH = -30                       # deg, at GRIP_TILT_FROM_H and above (-30 = mostly forward)
GRIP_TILT_FROM_H = 0.16                   # m: above this height the gripper is fully tilted forward

# --- feel (relative "clutch" control + One-Euro smoothing) ---
MOVE_SCALE = 1.0                          # 1.0 = real-life 1:1 (hand moves 10 cm -> gripper moves 10 cm)
BASE_DEG_PER_M = 200                      # hand 10 cm left/right -> base turns 20 deg
READY = (90.0, 0.27, 0.12)                # where the arm starts when your hand appears: base deg, reach m, height m
FILTER_MIN_CUTOFF = 0.8                   # One-Euro: lower = steadier when your hand is still (more lag)
FILTER_BETA = 6.0                         # One-Euro: higher = less lag when you move fast
GRIP_STEP = 15                            # gripper degrees per packet (gripper may move faster than the arm)
SEND_HZ = 25
NO_HAND_HOME_S = 2.0
MAX_DEG_PER_SEND = 6                      # safety speed limit per joint per packet (6 deg x 25 Hz = 150 deg/s)
START_FRAMES = 8                          # ~0.3 s of steady hand before the arm starts following
GESTURE_FRAMES = 6                        # a gesture must be seen this many frames in a row (~0.2 s) before it counts
# =================================================================


def lerp_clamped(v, src, dst):
    t = (v - src[0]) / (src[1] - src[0])
    t = min(1.0, max(0.0, t))
    return dst[0] + t * (dst[1] - dst[0])


class OneEuro:
    """One-Euro filter (Casiez et al., CHI 2012) for a 3D point. Smooth when slow, responsive when fast."""
    def __init__(self, min_cutoff=FILTER_MIN_CUTOFF, beta=FILTER_BETA, d_cutoff=1.0):
        self.mc, self.beta, self.dc = min_cutoff, beta, d_cutoff
        self.reset()

    def reset(self):
        self.x = self.dx = self.t = None

    @staticmethod
    def _alpha(cutoff, dt):
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x, t):
        x = np.asarray(x, float)
        if self.x is None:
            self.x, self.dx, self.t = x, np.zeros_like(x), t
            return x
        dt = max(1e-3, t - self.t)
        self.t = t
        dx = (x - self.x) / dt
        a_d = self._alpha(self.dc, dt)
        self.dx = a_d * dx + (1 - a_d) * self.dx
        cutoff = self.mc + self.beta * float(np.linalg.norm(self.dx))
        a = self._alpha(cutoff, dt)
        self.x = a * x + (1 - a) * self.x
        return self.x


def relative_target(hand, anchor_hand, anchor_tip):
    """Clutch-anchored relative mapping: the gripper moves by how much your hand moved since the anchor."""
    dx, dy, dz = (np.asarray(hand) - np.asarray(anchor_hand))
    if MIRROR_X:
        dx = -dx
    base = anchor_tip[0] + math.degrees(dx / max(0.15, anchor_tip[1])) * MOVE_SCALE   # sideways cm -> same cm at the gripper
    height = anchor_tip[2] + (-dy) * MOVE_SCALE                    # hand up (y negative) -> gripper up
    reach = anchor_tip[1] + ((-dz) if NEAR_MEANS_FAR else dz) * MOVE_SCALE
    return (min(BASE_RANGE[1], max(BASE_RANGE[0], base)),
            min(REACH[1], max(REACH[0], reach)),
            min(HEIGHT[1], max(HEIGHT[0], height)))


def hand_to_target(wrist_xyz, mirror=MIRROR_X):
    """Hand position (camera frame, m) -> (base_deg, reach_m, height_m)."""
    x, y, z = wrist_xyz
    if mirror:
        x = -x
    base = lerp_clamped(x, HAND_X, BASE_RANGE)
    reach = lerp_clamped(z, HAND_Z, REACH[::-1] if NEAR_MEANS_FAR else REACH)
    height = lerp_clamped(-y, (-HAND_Y[1], -HAND_Y[0]), HEIGHT)   # hand up (y negative) -> higher
    return base, reach, height


def within_limits(a1, a2, a3):
    """True if the pose fits every servo's range WITHOUT clamping (so the arm really reaches the target)."""
    rel = [90 + SHOULDER_SIGN * (a1 - 90) + SHOULDER_OFFSET, 90 + ELBOW_SIGN * (a2 - a1) + ELBOW_OFFSET,
           90 + WRIST_SIGN * (a3 - a2) + WRIST_OFFSET]
    if a1 > UPPER_ARM_MAX_DEG:            # natural pose only: upper arm never leans back over the base
        return False                      # (stops the arm folding over itself with the wrist jammed down)
    return all(LO[i + 1] + 2 <= v <= HI[i + 1] - 2 for i, v in enumerate(rel))


def ik(reach, height):
    """Planar IK. Returns absolute link angles (deg from horizontal) a1 (upper arm), a2 (forearm), a3 (gripper)
    or None if unreachable within the servo limits. Prefers the gripper pointing straight down (best for
    picking), then gradually flattens it. Tries both elbow bends and keeps the first that fits the limits."""
    # gripper angle changes with height, like a human hand: near the table it points DOWN (to pick),
    # higher up it tilts forward (relaxed). Then try nearby angles if that one is out of servo range.
    k = min(1.0, max(0.0, (height - HEIGHT[0]) / (GRIP_TILT_FROM_H - HEIGHT[0])))
    want = APPROACH_LOW + k * (APPROACH_HIGH - APPROACH_LOW)
    for phi in sorted(range(-150, -4, 5), key=lambda a: abs(a - want)):
        p = math.radians(phi)
        wr = reach - L3 * math.cos(p)                   # wrist position relative to the shoulder joint
        wh = height - L0 - L3 * math.sin(p)
        d2 = wr * wr + wh * wh
        c = (d2 - L1 * L1 - L2 * L2) / (2 * L1 * L2)
        if abs(c) > 1:
            continue
        for q2 in (-math.acos(c), math.acos(c)):         # elbow bent one way, then the other
            q1 = math.atan2(wh, wr) - math.atan2(L2 * math.sin(q2), L1 + L2 * math.cos(q2))
            a1, a2 = math.degrees(q1), math.degrees(q1 + q2)
            if within_limits(a1, a2, float(phi)):
                return a1, a2, float(phi)
    return None


def fk(a1, a2, a3):
    """Absolute link angles -> 2D points (r, h) of shoulder, elbow, wrist, tip. Used for drawing + tests."""
    pts = [(0.0, 0.0), (0.0, L0)]
    for L, a in ((L1, a1), (L2, a2), (L3, a3)):
        r, h = pts[-1]
        pts.append((r + L * math.cos(math.radians(a)), h + L * math.sin(math.radians(a))))
    return pts


def to_servos(base, a1, a2, a3, twist, grip):
    """Absolute angles -> Braccio servo degrees. Candle pose (all links vertical) = 90,90,90."""
    shoulder = 90 + SHOULDER_SIGN * (a1 - 90) + SHOULDER_OFFSET
    elbow = 90 + ELBOW_SIGN * (a2 - a1) + ELBOW_OFFSET
    wrist = 90 + WRIST_SIGN * (a3 - a2) + WRIST_OFFSET
    s = [base, shoulder, elbow, wrist, twist, grip]
    return [int(round(min(HI[i], max(LO[i], v)))) for i, v in enumerate(s)]


def servos_to_abs(s):
    """Inverse of to_servos (for drawing what the arm will actually do after clamping)."""
    a1 = 90 + (s[1] - 90 - SHOULDER_OFFSET) / SHOULDER_SIGN
    a2 = a1 + (s[2] - 90 - ELBOW_OFFSET) / ELBOW_SIGN
    a3 = a2 + (s[3] - 90 - WRIST_OFFSET) / WRIST_SIGN
    return a1, a2, a3


def palm_roll_deg(p_index_mcp, p_pinky_mcp):
    """Angle of the knuckle line in the camera's x-y plane. Flat palm facing camera ~ 0."""
    dx, dy = p_index_mcp[0] - p_pinky_mcp[0], p_index_mcp[1] - p_pinky_mcp[1]
    return math.degrees(math.atan2(dy, dx))


def draw_sim(servos, status):
    import cv2
    img = np.full((360, 420, 3), 255, np.uint8)
    a1, a2, a3 = servos_to_abs(servos)
    pts = fk(a1, a2, a3)
    sc, ox, oy = 520, 60, 320
    P = [(int(ox + r * sc), int(oy - h * sc)) for r, h in pts]
    cv2.line(img, (20, oy), (400, oy), (180, 180, 180), 2)                       # table
    cols = [(90, 90, 90), (200, 120, 40), (40, 140, 200), (40, 170, 60)]
    for i in range(4):
        cv2.line(img, P[i], P[i + 1], cols[i], 6)
    for p in P:
        cv2.circle(img, p, 5, (0, 0, 0), -1)
    names = ["Base", "Shoulder", "Elbow", "Wrist", "Twist", "Grip"]
    for i, (n, v) in enumerate(zip(names, servos)):
        cv2.putText(img, f"M{i+1} {n}: {v}", (250, 25 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    cv2.putText(img, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1)
    cv2.putText(img, "side view (reach ->)", (10, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (120, 120, 120), 1)
    return img


class Sender:
    def __init__(self, ip):
        self.ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) if ip else None

    def send(self, servos):
        if self.sock:
            self.sock.sendto(",".join(map(str, servos)).encode(), (self.ip, PORT))


def run_check(sender, show=False):
    """Send 3 slow known poses so you can compare the real arm with the simulation drawing."""
    tests = [("CANDLE: every link straight up", HOME),
             ("REACH FORWARD LOW: gripper ~22 cm out, ~5 cm above table", None),
             ("REACH FORWARD HIGH: gripper ~28 cm out, ~18 cm above table", None)]
    try:
        _run_check_poses(sender, tests, show)
    finally:
        sender.send(HOME)                # STOP / Ctrl+C during the check still sends the arm home
    print("\nIf a joint went the opposite way to the description, flip its *_SIGN at the top of this file.")


def _run_check_poses(sender, tests, show):
    for name, pose in tests:
        if pose is None:
            sol = ik(0.22, 0.05) if "LOW" in name else ik(0.28, 0.18)
            pose = to_servos(90, *sol, 90, GRIP_OPEN)
        print(f"\n{name}\n  sending {pose}  (holding 4 s)")
        t0 = time.time()
        while time.time() - t0 < 4:
            sender.send(pose)
            if show:
                import cv2
                cv2.imshow("Braccio simulation", draw_sim(pose, name.split(":")[0]))
                cv2.waitKey(100)
            else:
                time.sleep(0.1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-ip", default=None, help="UNO R4 IP. Leave out = simulation only (nothing sent)")
    ap.add_argument("--show", action="store_true", help="show camera + simulated arm windows")
    ap.add_argument("--check", action="store_true", help="send 3 test poses and exit")
    ap.add_argument("--model", default=os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task"))
    args = ap.parse_args()

    sender = Sender(args.arm_ip)
    if args.check:
        if not args.arm_ip:
            raise SystemExit("--check needs --arm-ip")
        run_check(sender, args.show)
        return
    print("LIVE: sending to arm at %s:%d" % (args.arm_ip, PORT) if args.arm_ip else "SIMULATION ONLY: nothing is sent")

    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    from rs_common import start_pipeline
    from hand_depth import (KEY_POINTS, WRIST, INDEX_MCP, PINKY_MCP, HAND_CONNECTIONS,
                            classify_gesture, depth_at_color_pixel)

    landmarker = vision.HandLandmarker.create_from_options(vision.HandLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=args.model),
        running_mode=vision.RunningMode.VIDEO, num_hands=1,
        min_hand_detection_confidence=0.6, min_tracking_confidence=0.5))
    rs, pipe, profile, scale = start_pipeline()
    d_prof = profile.get_stream(rs.stream.depth).as_video_stream_profile()
    c_prof = profile.get_stream(rs.stream.color).as_video_stream_profile()
    d_intr, c_intr = d_prof.get_intrinsics(), c_prof.get_intrinsics()
    d2c, c2d = d_prof.get_extrinsics_to(c_prof), c_prof.get_extrinsics_to(d_prof)

    stable, cand, cand_count = "open", None, 0   # debounced gesture
    roll_neutral = None           # palm roll when the hand first appears = wrist twist centre
    target = None                 # current gripper target (base, reach, height, twist)
    anchor_hand = None            # hand position when following (re)started
    anchor_tip = None             # gripper target at that moment
    filt = OneEuro()
    seen_frames = 0               # hand must be steady in view ~0.3 s before the arm moves (ignores false detections)
    servos = list(HOME)
    sent = list(HOME)             # what the arm was last told (rate-limited version of servos)
    paused = False
    grip = GRIP_OPEN
    last_seen = time.time()
    last_send = 0
    t0 = time.time()
    try:
        while True:
            frames = pipe.wait_for_frames()
            df, cf = frames.get_depth_frame(), frames.get_color_frame()
            if not df or not cf:
                continue
            color = np.asanyarray(cf.get_data())
            depth_img = np.asanyarray(df.get_data())
            res = landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(color, cv2.COLOR_BGR2RGB)),
                int((time.time() - t0) * 1000))

            status = "no hand (holding)"
            gesture = None
            if not res.hand_landmarks:
                anchor_hand = None
                filt.reset()
                seen_frames = 0
            if res.hand_landmarks:
                lms = res.hand_landmarks[0]
                px = {i: (lm.x * c_intr.width, lm.y * c_intr.height) for i, lm in enumerate(lms)}
                pts = {}
                for i in KEY_POINTS:
                    z = depth_at_color_pixel(rs, df, depth_img, scale, d_intr, c_intr, d2c, c2d, *px[i])
                    if z > 0:
                        pts[i] = np.array(rs.rs2_deproject_pixel_to_point(c_intr, list(px[i]), z))
                if WRIST not in pts or not (ZONE[0] <= pts[WRIST][2] <= ZONE[1]):
                    anchor_hand = None
                    filt.reset()
                    seen_frames = 0
                if WRIST not in pts:
                    status = "hand seen, no depth at wrist (holding)"
                elif not (ZONE[0] <= pts[WRIST][2] <= ZONE[1]):
                    status = f"hand outside zone Z {pts[WRIST][2]:.2f} m (holding)"
                if WRIST in pts and ZONE[0] <= pts[WRIST][2] <= ZONE[1]:
                    last_seen = time.time()
                    # gesture from MediaPipe's own 3D hand model (metres, no camera depth noise) - much steadier
                    wl = getattr(res, "hand_world_landmarks", None)
                    if wl:
                        raw = classify_gesture({i: np.array([l.x, l.y, l.z]) for i, l in enumerate(wl[0])})
                    else:
                        raw = classify_gesture(pts)
                    # debounce: only switch gesture after it has been seen GESTURE_FRAMES frames in a row
                    raw = {"pinch": "fist"}.get(raw, raw)   # pinch counts as closing
                    if raw == cand:
                        cand_count += 1
                    else:
                        cand, cand_count = raw, 1
                    # open palm -> OPEN, fist (or pinch) -> CLOSED; anything in between keeps the last state
                    hand_state = {"open": "open", "fist": "fist", "pinch": "fist"}.get(raw)
                    if hand_state and cand_count >= GESTURE_FRAMES:
                        stable = hand_state
                    gesture = stable
                    if hand_state != stable:
                        # hand is changing shape (opening/closing): hold the arm still so it doesn't drift,
                        # and re-anchor afterwards so it carries on from exactly here
                        status = f"{stable} - changing hand shape (arm holding)"
                        anchor_hand = None
                        filt.reset()
                    elif seen_frames < START_FRAMES:
                        seen_frames += 1
                        filt(pts[WRIST], time.time())          # warm up the filter while waiting
                        status = "hand found - hold still..."
                    else:
                        hand = filt(pts[WRIST], time.time())
                        if CONTROL_MODE == "absolute":
                            b, r, h = hand_to_target(hand)
                        else:
                            if anchor_hand is None:
                                anchor_hand = hand
                                anchor_tip = tuple(target[:3]) if target is not None else READY
                            b, r, h = relative_target(hand, anchor_hand, anchor_tip)
                        tw = 90.0 if target is None else float(target[3])   # default: keep the current twist
                        if not TWIST_ENABLED:
                            tw = 90.0
                        elif INDEX_MCP in pts and PINKY_MCP in pts:
                            knuckles = pts[INDEX_MCP] - pts[PINKY_MCP]
                            # only trust the angle when the knuckle line is clearly visible (palm facing the camera)
                            if math.hypot(knuckles[0], knuckles[1]) > 0.04:
                                roll = palm_roll_deg(pts[INDEX_MCP], pts[PINKY_MCP])
                                if roll_neutral is None or target is None:
                                    roll_neutral = roll      # however you first hold your hand = twist 90 (centre)
                                diff = (roll - roll_neutral + 180) % 360 - 180
                                if abs(diff) < TWIST_DEADBAND:
                                    diff = 0.0
                                else:
                                    diff -= math.copysign(TWIST_DEADBAND, diff)
                                tw = min(180, max(0, 90 + TWIST_SIGN * diff))
                        target = np.array([b, r, h, tw])
                        grip = GRIP_CLOSED if gesture == "fist" else GRIP_OPEN
                        sol = ik(target[1], target[2])
                        if not sol:                       # too close/low for a natural pose: use the nearest spot it CAN reach
                            for dr in np.arange(0.01, 0.12, 0.01):
                                sol = ik(min(REACH[1], target[1] + dr), target[2]) or ik(target[1], target[2] + dr)
                                if sol:
                                    break
                        if sol:
                            servos = to_servos(target[0], *sol, target[3], grip)
                            status = f"{gesture} reach {target[1]*100:.0f}cm height {target[2]*100:.0f}cm"
                        else:
                            status = "out of reach - holding"
                if args.show:
                    for a, b2 in HAND_CONNECTIONS:
                        cv2.line(color, tuple(map(int, px[a])), tuple(map(int, px[b2])), (0, 255, 0), 2)

            if time.time() - last_seen > NO_HAND_HOME_S:
                servos = list(HOME)
                target = None
                anchor_hand = anchor_tip = None
                filt.reset()
                seen_frames = 0
                stable, cand, cand_count = "open", None, 0
                roll_neutral = None
                status = "no hand -> HOME"

            if paused:
                status = "PAUSED (space to resume)"
            if time.time() - last_send > 1.0 / SEND_HZ:
                if not paused:
                    # move at most MAX_DEG_PER_SEND per joint per packet: no sudden jumps, even after fist/home
                    lim = [MAX_DEG_PER_SEND] * 5 + [GRIP_STEP]
                    sent = [int(round(p + max(-l, min(l, t - p)))) for p, t, l in zip(sent, servos, lim)]
                sender.send(sent)            # keep sending even when frozen/paused, so the arm holds its pose
                last_send = time.time()
                print(f"{status:45s} -> {sent}")

            if args.show:
                cv2.putText(color, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.imshow("Hand (q = quit)", color)
                cv2.imshow("Braccio simulation", draw_sim(sent, "LIVE" if args.arm_ip else "SIMULATION"))
                k = cv2.waitKey(1) & 0xFF
                if k == ord("q"):
                    break
                if k == ord(" "):
                    paused = not paused
    except KeyboardInterrupt:
        pass
    finally:
        sender.send(HOME)
        pipe.stop()
        landmarker.close()


if __name__ == "__main__":
    main()
