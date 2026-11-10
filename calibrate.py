"""Braccio calibration: make the real arm match the simulation, then save the corrections.

Why: if a servo's "90" is a few degrees off, or a joint bends the other way, the gripper ends up
several cm away from where the code thinks it is (e.g. it won't go down to the table).

How: the arm holds a known pose. You nudge each joint's offset until the REAL arm matches the
description, then type `save`. hand_to_braccio.py loads calibration.json automatically.

    python calibrate.py [--arm-ip 192.168.1.100]

Keep a hand on the arm's 5V plug.
"""
import argparse
import json
import os
import threading
import time

import hand_to_braccio as H

HERE = os.path.dirname(os.path.abspath(__file__))
POSES = {
    "1": ("CANDLE", None, None,
          "Every link points straight up. Check from the SIDE (shoulder, elbow, wrist) with a square or phone level."),
    "2": ("REACH LOW", 0.22, 0.05,
          "Gripper TIP 22 cm in front of the base's centre, 5 cm above the surface the arm stands on."),
    "3": ("REACH HIGH", 0.28, 0.18,
          "Gripper TIP 28 cm in front of the base's centre, 18 cm above the surface the arm stands on."),
    "4": ("REACH FAR", 0.30, 0.08,
          "Gripper TIP 30 cm in front of the base's centre, 8 cm above the surface the arm stands on."),
}

HELP = """
Commands (type and press Enter):
  1 / 2 / 3 / 4      choose pose: 1 candle, 2 reach low, 3 reach high, 4 reach far
  s+2  s-2           shoulder offset up/down by 2 degrees (any number works, e.g. s+5)
  e+2  e-2           elbow offset
  w+2  w-2           wrist (up/down) offset
  flip s|e|w         that joint bends the OPPOSITE way to the description -> flip its direction
  base 75            height of the shoulder axle above the surface, in mm (default 71.5)
  show               print current settings
  save               save to calibration.json (used by LIVE automatically)
  q                  quit (arm goes to candle)

Suggested order: 1 (candle) -> fix s/e/w until straight up -> 2 (reach low) -> measure with a ruler ->
small s/e/w nudges until the tip is right -> check 3 and 4 -> save.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-ip", default=None)
    args = ap.parse_args()
    ip = args.arm_ip
    if not ip:
        try:
            with open(os.path.join(HERE, "arm_ip.txt")) as f:
                ip = f.read().strip()
        except OSError:
            ip = "192.168.1.100"
    sender = H.Sender(ip)
    state = {"pose": "1", "servos": list(H.HOME), "run": True}

    def compute():
        name, r, h, _ = POSES[state["pose"]]
        if r is None:
            sv = [90, 90 + H.SHOULDER_OFFSET, 90 + H.ELBOW_OFFSET, 90 + H.WRIST_OFFSET, 90, H.GRIP_OPEN]
        else:
            sol = H.ik(r, h)
            if sol is None:
                print("  !! That pose is outside the servo limits with these settings - try smaller offsets.")
                return
            sv = H.to_servos(90, *sol, 90, H.GRIP_OPEN)
        state["servos"] = [int(max(H.LO[i], min(H.HI[i], v))) for i, v in enumerate(sv)]

    def show():
        name, _, _, check = POSES[state["pose"]]
        print(f"\n[{name}] sending {state['servos']}")
        print(f"  CHECK: {check}")
        print(f"  offsets  shoulder {H.SHOULDER_OFFSET:+}  elbow {H.ELBOW_OFFSET:+}  wrist {H.WRIST_OFFSET:+}"
              f"   signs  s {H.SHOULDER_SIGN:+} e {H.ELBOW_SIGN:+} w {H.WRIST_SIGN:+}   base {H.L0*1000:.1f} mm")

    def sender_loop():
        while state["run"]:
            sender.send(state["servos"])
            time.sleep(0.1)

    print(f"Calibrating arm at {ip}:{H.PORT}.  Keep a hand on the 5V plug.")
    print(HELP)
    compute(); show()
    threading.Thread(target=sender_loop, daemon=True).start()

    try:
        while True:
            cmd = input("> ").strip().lower().replace(" ", "")
            if not cmd:
                continue
            if cmd in POSES:
                state["pose"] = cmd
            elif cmd[0] in "sew" and len(cmd) > 1 and cmd[1] in "+-":
                try:
                    d = int(cmd[1:])
                except ValueError:
                    print("  use e.g. s+2 or e-5"); continue
                if abs(d) > 20:
                    print("  max 20 degrees per step"); continue
                if cmd[0] == "s":
                    H.SHOULDER_OFFSET += d
                elif cmd[0] == "e":
                    H.ELBOW_OFFSET += d
                else:
                    H.WRIST_OFFSET += d
            elif cmd.startswith("flip") and len(cmd) == 5 and cmd[4] in "sew":
                attr = {"s": "SHOULDER_SIGN", "e": "ELBOW_SIGN", "w": "WRIST_SIGN"}[cmd[4]]
                setattr(H, attr, -getattr(H, attr))
            elif cmd.startswith("base"):
                try:
                    mm = float(cmd[4:])
                    if not 30 <= mm <= 200:
                        raise ValueError
                    H.L0 = mm / 1000
                except ValueError:
                    print("  e.g. base 75  (mm, between 30 and 200)"); continue
            elif cmd == "show":
                pass
            elif cmd == "save":
                data = {"shoulder_offset": H.SHOULDER_OFFSET, "elbow_offset": H.ELBOW_OFFSET,
                        "wrist_offset": H.WRIST_OFFSET, "shoulder_sign": H.SHOULDER_SIGN,
                        "elbow_sign": H.ELBOW_SIGN, "wrist_sign": H.WRIST_SIGN, "base_mm": round(H.L0 * 1000, 1)}
                with open(H.CAL_FILE, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"  saved {H.CAL_FILE}: {data}")
                continue
            elif cmd in ("q", "quit", "exit"):
                break
            else:
                print(HELP); continue
            compute(); show()
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        state["pose"] = "1"; compute()
        state["run"] = False
        time.sleep(0.15)
        for _ in range(5):
            sender.send(state["servos"]); time.sleep(0.05)
        print("\nArm sent to candle. Bye.")
        try:
            input("Press Enter to close this window.")
        except EOFError:
            pass


if __name__ == "__main__":
    main()
