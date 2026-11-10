---
tags: [terminal, cheatsheet]
aliases: [Commands]
---
# Terminal Commands Cheat Sheet

All commands assume the project is in `~/braccio-vision` and the venv is `~/braccio-venv`.

> [!tip] Start every terminal session with
> ```bash
> source ~/braccio-venv/bin/activate
> cd ~/braccio-vision
> ```

## 🛠️ One-time setup
```bash
bash setup_pi.sh                 # install camera driver + libraries + hand model (45-90 min)
sudo reboot
bash install_shortcuts.sh        # desktop icon "Braccio Control Panel"
```

## 📷 Camera
```bash
rs-enumerate-devices             # is the D435 detected? (look for "USB Type Descriptor: 3.2")
rs-enumerate-devices | grep -i usb
python check_camera.py           # 10-second test: FPS, centre distance, valid depth %
python check_camera.py --show    # live colour + depth window (q = quit)
realsense-viewer                 # Intel's own viewer app (built by setup)
vcgencmd get_config usb_max_current_enable    # should print =1
```

## ✋ Hand and objects (no arm)
```bash
python hand_depth.py --show      # hand skeleton, gesture, wrist X/Y/Z in metres
python objects_depth.py --show   # table detection + objects with heights (r = re-detect, q = quit)
```

## 🦾 Arm
```bash
python hand_to_braccio.py --show                                  # SIMULATION: arm does not move
python hand_to_braccio.py --check --show --arm-ip 192.168.1.100   # 3 test poses
python hand_to_braccio.py --show --arm-ip 192.168.1.100           # LIVE
python calibrate.py --arm-ip 192.168.1.100                        # calibration tool
python joint_test.py                                              # one joint at a time
```

### Calibration commands inside calibrate.py
| Type | Does |
|---|---|
| `1` `2` `3` `4` | pose: candle, reach low, reach high, reach far |
| `s+2` / `s-2` | shoulder offset ± 2° (any number up to 20) |
| `e+2` / `e-2` | elbow offset |
| `w+2` / `w-2` | wrist offset |
| `flip s` | shoulder bends the wrong way: reverse it (also `flip e`, `flip w`) |
| `base 75` | shoulder axle height above the board in mm |
| `show` | print current settings |
| `save` | write `calibration.json` |
| `q` | quit (arm goes to candle) |

Your current calibration: **shoulder −12, wrist −10**. See it with:
```bash
cat ~/braccio-vision/calibration.json
```

## 🌐 Network
```bash
ping -c 3 192.168.1.100          # is the arm reachable? (3 tries)
iwgetid -r                       # which WiFi is the Pi on?
nmcli dev wifi                   # list WiFi networks
nmcli connection up id BraccioNet   # join BraccioNet (if saved)
hostname -I                      # the Pi's own IP address
```

## 🖥️ Control Panel
```bash
~/braccio-venv/bin/python ~/braccio-vision/control_panel.py      # start it from a terminal (shows errors)
```

## ✏️ Editing a setting quickly
```bash
nano ~/braccio-vision/hand_to_braccio.py                         # edit by hand (Ctrl+O save, Ctrl+X exit)
grep -n "MIRROR_X =" hand_to_braccio.py                          # find a setting and its line number
sed -i 's/^MIRROR_X = True/MIRROR_X = False/' hand_to_braccio.py # replace it in one line
```
`sed -i 's/OLD/NEW/' file` means "in the file, replace OLD with NEW". The `^` means "at the start of the line".

## 📦 Updating from the USB drive
```bash
cp /media/braccio/*/hand_to_braccio.py ~/braccio-vision/
cp /media/braccio/*/calibrate.py ~/braccio-vision/
```
See [[Copying Files via USB]].

## 🧯 When things hang
| Problem | Command |
|---|---|
| A script won't stop | **Ctrl+C** in its terminal, or the panel's STOP |
| Camera "busy" | `pkill -f hand_to_braccio.py` then try again |
| Which Python scripts are running? | `ps aux \| grep python` |
| Pi temperature (no cooler yet!) | `vcgencmd measure_temp` |
| Free disk space | `df -h` |
