"""Joint test: moves ONE joint at a time so you can see if the real arm matches the numbers.
Stand at the SIDE of the arm and take a photo at each step (the terminal tells you when).

    ~/braccio-venv/bin/python ~/braccio-vision/joint_test.py
"""
import socket, time, os, sys

IP = sys.argv[1] if len(sys.argv) > 1 else (
    open(os.path.expanduser("~/braccio-vision/arm_ip.txt")).read().strip()
    if os.path.exists(os.path.expanduser("~/braccio-vision/arm_ip.txt")) else "192.168.1.100")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

STEPS = [
    ("1 CANDLE: whole arm straight up", [90, 90, 90, 90, 90, 20]),
    ("2 SHOULDER 45: whole straight arm should lean FORWARD ~45 deg (like half-way to the table)", [90, 45, 90, 90, 90, 20]),
    ("3 + ELBOW 45: forearm should bend a further ~45 deg forward/down", [90, 45, 45, 90, 90, 20]),
    ("4 + WRIST 45: gripper should bend a further ~45 deg down", [90, 45, 45, 45, 90, 20]),
    ("5 THE POSE FROM YOUR PHOTO (gripper should be ~5 cm above table)", [90, 47, 67, 6, 90, 20]),
]


def hold(pose, seconds):
    end = time.time() + seconds
    while time.time() < end:
        sock.sendto(",".join(map(str, pose)).encode(), (IP, 5005))
        time.sleep(0.1)


print(f"Sending to arm at {IP}:5005. Keep a hand near the 5V plug. Ctrl+C = stop.\n")
try:
    for text, pose in STEPS:
        print(f"{text}\n   servos {pose}  -> PHOTO NOW (holding 8 s)\n")
        hold(pose, 8)
finally:
    print("back to candle")
    hold([90, 90, 90, 90, 90, 20], 3)
