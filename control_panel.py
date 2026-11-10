"""Braccio Control Panel - one window to start everything.

Buttons: LIVE (real arm), Simulation, Arm Check, Camera Test, STOP.
Status lights: camera connected? arm reachable? Output of the running mode is shown in the log.
Started from the desktop icon "Braccio Control Panel" (see install_shortcuts.sh).
"""
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("tkinter missing. Install it with:  sudo apt install -y python3-tk")
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ARM_IP = "192.168.1.100"
ARM_WIFI = "BraccioNet"                          # the router network the arm is on
IP_FILE = os.path.join(HERE, "arm_ip.txt")      # remembers the arm address you type in the panel
PY = sys.executable                              # the braccio-venv python that started this panel

ENV = dict(os.environ, QT_QPA_FONTDIR="/usr/share/fonts/truetype/dejavu", PYTHONUNBUFFERED="1")

GREEN, RED, GREY, AMBER = "#2e9d4f", "#c0392b", "#9a9a9a", "#d4880f"


def load_ip():
    try:
        with open(IP_FILE) as f:
            return f.read().strip() or DEFAULT_ARM_IP
    except OSError:
        return DEFAULT_ARM_IP


def camera_present():
    code = "import pyrealsense2 as rs,sys; sys.exit(0 if len(rs.context().query_devices()) else 1)"
    try:
        return subprocess.run([PY, "-c", code], cwd=HERE, env=ENV, timeout=8,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except Exception:
        return False


def current_wifi():
    for cmd in (["iwgetid", "-r"], ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=4).stdout
        except Exception:
            continue
        if cmd[0] == "iwgetid" and out.strip():
            return out.strip()
        for line in out.splitlines():
            if line.startswith("yes:"):
                return line[4:]
    return ""


def connect_wifi(name):
    """Try a saved connection first, then a plain connect (works if the password is saved)."""
    for cmd in (["nmcli", "connection", "up", "id", name], ["nmcli", "dev", "wifi", "connect", name]):
        try:
            if subprocess.run(cmd, capture_output=True, timeout=25).returncode == 0:
                return True
        except Exception:
            pass
    return False


def arm_reachable(ip):
    try:
        return subprocess.run(["ping", "-c", "1", "-W", "1", ip], timeout=4,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except Exception:
        return False


class Panel:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.mode = None
        self.q = queue.Queue()
        self.rec = None                  # screen recorder process (wf-recorder)
        root.title("Braccio Control Panel")
        root.configure(bg="white")
        root.minsize(600, 830)

        tk.Label(root, text="Braccio gesture control", font=("Sans", 18, "bold"), bg="white").pack(pady=(14, 2))
        tk.Label(root, text="Emergency stop: pull the arm's 5V plug", font=("Sans", 10), fg=RED, bg="white").pack()

        # --- before-you-start checklist
        ck = tk.LabelFrame(root, text=" Before you start ", bg="white", font=("Sans", 10, "bold"), padx=10, pady=4)
        ck.pack(fill="x", padx=12, pady=(8, 0))
        for line in ["1. Router (BraccioNet) on - wait about 1 min",
                     "2. Arm: plug in 5V (it moves to start pose - keep clear), wait ~10 s",
                     f"3. Pi on the {ARM_WIFI} WiFi (light below green, or press Connect)",
                     "4. D435 camera in a BLUE USB port",
                     "5. Quest app closed - only one controller at a time",
                     "6. First run today: press ARM CHECK, then LIVE"]:
            tk.Label(ck, text=line, bg="white", anchor="w", justify="left").pack(fill="x")

        # --- status row
        st = tk.Frame(root, bg="white")
        st.pack(pady=10)
        self.wifi_light = self._light(st, "WiFi")
        self.wifi_btn = tk.Button(st, text=f"Connect {ARM_WIFI}", command=self.connect)
        self.wifi_btn.pack(side="left", padx=(4, 0))
        self.cam_light = self._light(st, "Camera")
        self.arm_light = self._light(st, "Arm")
        tk.Label(st, text="Arm IP", bg="white").pack(side="left", padx=(16, 4))
        self.ip = tk.StringVar(value=load_ip())
        tk.Entry(st, textvariable=self.ip, width=15).pack(side="left")
        tk.Button(st, text="Re-check", command=self.refresh).pack(side="left", padx=6)

        # --- mode buttons
        bf = tk.Frame(root, bg="white")
        bf.pack(pady=4)
        self.buttons = []
        for text, sub, colour, cmd in [
            ("LIVE", "hand controls the real arm", GREEN, self.start_live),
            ("Simulation", "arm does not move", "#3b6fb6", self.start_sim),
            ("Arm check", "3 slow test poses", AMBER, self.start_check),
            ("Camera test", "colour + depth view", "#6b5bb5", self.start_camera),
            ("Calibrate arm", "match real arm to the model", "#555555", self.start_calibrate),
        ]:
            b = tk.Button(bf, text=f"{text}\n{sub}", width=22, height=3, bg=colour, fg="white",
                          activebackground=colour, font=("Sans", 11, "bold"), command=cmd)
            b.pack(pady=4)
            self.buttons.append(b)

        self.stop_btn = tk.Button(root, text="STOP  (arm goes home)", width=22, height=2, bg=RED, fg="white",
                                  activebackground=RED, font=("Sans", 11, "bold"), command=self.stop,
                                  state="disabled")
        self.stop_btn.pack(pady=(6, 4))

        self.rec_btn = tk.Button(root, text="\u25CF  Record screen", width=22, bg="#222", fg="white",
                                 activebackground="#444", font=("Sans", 10, "bold"), command=self.toggle_record)
        self.rec_btn.pack(pady=(0, 4))

        self.status = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status, bg="white", font=("Sans", 11)).pack()
        tk.Label(root, text="In the camera window: SPACE = pause, Q = quit", bg="white", fg="#666").pack()

        # --- log
        self.log = tk.Text(root, height=10, bg="#111", fg="#ddd", font=("Monospace", 9), wrap="none")
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(200, self.pump)
        root.after(300, self.refresh)

    # ---------- UI helpers
    def _light(self, parent, label):
        c = tk.Canvas(parent, width=18, height=18, bg="white", highlightthickness=0)
        c.pack(side="left", padx=(10, 2))
        dot = c.create_oval(2, 2, 16, 16, fill=GREY, outline="")
        tk.Label(parent, text=label, bg="white").pack(side="left")
        return (c, dot)

    def set_light(self, light, ok):
        c, dot = light
        c.itemconfig(dot, fill=GREY if ok is None else (GREEN if ok else RED))

    def write(self, line):
        self.log.insert("end", line)
        if int(self.log.index("end-1c").split(".")[0]) > 400:      # keep the log short
            self.log.delete("1.0", "100.0")
        self.log.see("end")

    def busy(self, running):
        for b in self.buttons:
            b.config(state="disabled" if running else "normal")
        self.stop_btn.config(state="normal" if running else "disabled")

    # ---------- status checks (in a thread so the window never freezes)
    def refresh(self):
        if self.proc:                      # don't touch the camera while a mode is using it
            return
        ip = self.ip.get().strip()
        try:
            with open(IP_FILE, "w") as f:
                f.write(ip)
        except OSError:
            pass
        self.set_light(self.cam_light, None)
        self.set_light(self.arm_light, None)
        self.status.set("Checking camera and arm...")

        self.set_light(self.wifi_light, None)

        def work():
            ssid = current_wifi()
            cam, arm = camera_present(), arm_reachable(ip)
            self.root.after(0, lambda: self._show_checks(cam, arm, ssid))
        threading.Thread(target=work, daemon=True).start()

    def _show_checks(self, cam, arm, ssid=""):
        self.cam_ok, self.arm_ok = cam, arm
        on_arm_net = ssid == ARM_WIFI or arm          # wired Ethernet to the router also counts if the arm answers
        self.set_light(self.wifi_light, on_arm_net)
        self.set_light(self.cam_light, cam)
        self.set_light(self.arm_light, arm)
        msg = []
        if not on_arm_net:
            msg.append(f"Pi on '{ssid or 'no WiFi'}' - connect to {ARM_WIFI}")
        if not cam:
            msg.append("Camera not found: D435 in a BLUE port, USB 3 cable")
        if not arm:
            msg.append(f"Arm not reachable at {self.ip.get().strip()}")
        self.status.set("\n".join(msg) if msg else "All green - ready. First run today: ARM CHECK, then LIVE")

    def connect(self):
        self.status.set(f"Connecting to {ARM_WIFI}...")
        self.wifi_btn.config(state="disabled")

        def work():
            ok = connect_wifi(ARM_WIFI)
            def done():
                self.wifi_btn.config(state="normal")
                if not ok:
                    messagebox.showinfo("WiFi", f"Couldn't connect automatically.\n\nClick the WiFi icon (top right of the "
                                        f"screen) and choose {ARM_WIFI}. Enter the router password once - "
                                        "the Pi remembers it after that.")
                self.refresh()
            self.root.after(0, done)
        threading.Thread(target=work, daemon=True).start()

    # ---------- run modes
    def run(self, label, args):
        if self.proc:
            return
        self.mode = label
        self.write(f"\n=== {label} ===\n")
        self.proc = subprocess.Popen([PY, "-u"] + args, cwd=HERE, env=ENV, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1,
                                     start_new_session=True)
        self.busy(True)
        self.status.set(f"Running: {label}")

        def reader(p):
            for line in p.stdout:
                if "QFontDatabase" in line or "Qt no longer ships fonts" in line:
                    continue
                self.q.put(line)
            p.wait()
            self.q.put(None)
        threading.Thread(target=reader, args=(self.proc,), daemon=True).start()

    def pump(self):
        try:
            while True:
                line = self.q.get_nowait()
                if line is None:
                    code = self.proc.returncode if self.proc else 0
                    self.write(f"=== {self.mode} finished (code {code}) ===\n")
                    self.proc = None
                    self.busy(False)
                    self.status.set("Ready")
                    self.root.after(500, self.refresh)
                else:
                    self.write(line)
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def need_camera(self):
        if not camera_present():
            messagebox.showerror("Camera", "Camera not found.\nPlug the D435 into a BLUE USB port (USB 3 cable).")
            self.set_light(self.cam_light, False)
            return False
        return True

    def start_live(self):
        if not self.need_camera():
            return
        ip = self.ip.get().strip()
        if not arm_reachable(ip):
            self.set_light(self.arm_light, False)
            if messagebox.askyesno("Arm not reachable",
                                   f"Arm not reachable at {ip}.\n\n- Arm 5V on? Wait ~10 s after power-on\n"
                                   "- Pi on the BraccioNet WiFi? (press Connect)\n- Quest app closed?\n\nRun SIMULATION instead?"):
                self.start_sim()
            return
        if messagebox.askokcancel("LIVE", "The real arm will move.\nArea clear and hand near the 5V plug?"):
            self.run("LIVE", ["hand_to_braccio.py", "--show", "--arm-ip", ip])

    def start_sim(self):
        if self.need_camera():
            self.run("SIMULATION", ["hand_to_braccio.py", "--show"])

    def start_check(self):
        ip = self.ip.get().strip()
        if not arm_reachable(ip):
            messagebox.showerror("Arm", f"Arm not reachable at {ip}.\nCheck 5V power, BraccioNet WiFi, Quest app closed.")
            self.set_light(self.arm_light, False)
            return
        if messagebox.askokcancel("Arm check", "3 slow test poses: candle, reach low, reach high.\n"
                                  "Compare the real arm with the simulation window.\n\nArea clear?"):
            self.run("ARM CHECK", ["hand_to_braccio.py", "--check", "--show", "--arm-ip", ip])

    def start_calibrate(self):
        ip = self.ip.get().strip()
        if not arm_reachable(ip):
            messagebox.showerror("Arm", f"Arm not reachable at {ip}.\nCheck 5V power, BraccioNet WiFi, Quest app closed.")
            return
        if self.proc:
            return
        if messagebox.askokcancel("Calibrate", "A terminal opens. The arm holds test poses while you type\n"
                                  "small corrections (e.g. s+2). Type 'save' when it matches.\n\nArea clear?"):
            subprocess.Popen(["lxterminal", "--title=Braccio calibration", "-e",
                              PY, os.path.join(HERE, "calibrate.py"), "--arm-ip", ip], cwd=HERE, env=ENV)

    def start_camera(self):
        if self.need_camera():
            self.run("CAMERA TEST", ["check_camera.py", "--show"])

    def stop(self):
        if not self.proc:
            return
        self.status.set("Stopping... (arm going home)")
        try:
            os.killpg(self.proc.pid, signal.SIGINT)        # like Ctrl+C: the script sends the arm HOME first
        except Exception:
            pass
        p = self.proc

        def force():
            time.sleep(4)
            if p.poll() is None:
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except Exception:
                    pass
        threading.Thread(target=force, daemon=True).start()

    # ---------- screen recording (wf-recorder, works on the Pi's Wayland desktop)
    def toggle_record(self):
        if self.rec:                                    # stop: Ctrl+C lets wf-recorder finish the file properly
            try:
                self.rec.send_signal(signal.SIGINT)
                self.rec.wait(timeout=5)
            except Exception:
                self.rec.kill()
            self.write(f"=== recording saved: {self.rec_file} ===\n")
            self.status.set(f"Recording saved to {self.rec_file}")
            self.rec = None
            self.rec_btn.config(text="\u25CF  Record screen", bg="#222")
            return
        if not shutil.which("wf-recorder"):
            messagebox.showinfo("Screen recording", "The recorder isn't installed yet. In a terminal run:\n\n"
                                "sudo apt install -y wf-recorder\n\nthen press Record again.")
            return
        folder = os.path.expanduser("~/Videos")
        os.makedirs(folder, exist_ok=True)
        self.rec_file = os.path.join(folder, time.strftime("braccio_%Y-%m-%d_%H-%M-%S.mp4"))
        self.rec = subprocess.Popen(["wf-recorder", "-f", self.rec_file],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        self.rec_btn.config(text="\u25A0  Stop recording", bg=RED)
        self.write(f"=== recording screen -> {self.rec_file} ===\n")
        self.status.set("Recording the screen... press Stop recording when done")

    def on_close(self):
        if self.rec:
            self.toggle_record()
        if self.proc:
            if not messagebox.askyesno("Quit", "A mode is still running. Stop it and quit?"):
                return
            self.stop()
            self.root.after(1500, self.root.destroy)
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    Panel(root)
    root.mainloop()
