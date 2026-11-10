---
tags: [terminal, linux, basics]
aliases: [Linux terminal, Shell basics]
---
# Terminal Basics

The **terminal** is a text window where you type commands for the Pi. The program reading your commands is called the **shell** (on the Pi it's `bash`).

## Reading the prompt
```
braccio@braccio-pi:~ $
```
| Part | Meaning |
|---|---|
| `braccio` | your **user name** |
| `braccio-pi` | the computer's name |
| `~` | the folder you're **in** right now (`~` = your home folder `/home/braccio`) |
| `$` | "ready, type a command" |

If you see `(braccio-venv)` at the start, the Python virtual environment is **active** (see below).

## Paths: how files are named
| Path | Means |
|---|---|
| `/` | the very top of the disk |
| `~` | your home folder, `/home/braccio` |
| `~/braccio-vision` | the project folder inside your home |
| `.` | "here" (the current folder) |
| `..` | "one folder up" |
| `/media/braccio/USB DEVICE` | where a USB drive appears when plugged in |

A path starting with `/` or `~` is **absolute**: it works from anywhere. Anything else is **relative** to the current folder.

## The commands you actually need

| Command | What it does | Example |
|---|---|---|
| `pwd` | print where you are | `pwd` |
| `ls` | list files | `ls ~/braccio-vision` |
| `ls -la` | list **all** files with sizes and dates | `ls -la` |
| `cd` | change folder | `cd ~/braccio-vision` · `cd ..` · `cd` (go home) |
| `cp` | copy | `cp a.py ~/braccio-vision/` |
| `mv` | move or rename | `mv old.py new.py` |
| `rm` | delete (**no recycle bin!**) | `rm test.txt` |
| `mkdir` | make a folder | `mkdir backups` |
| `cat` | print a file | `cat calibration.json` |
| `nano` | simple text editor (save: **Ctrl+O, Enter**; exit: **Ctrl+X**) | `nano hand_to_braccio.py` |
| `grep` | search for text in files | `grep GRIP_OPEN hand_to_braccio.py` |
| `ping` | is a device reachable? (Ctrl+C to stop) | `ping 192.168.1.100` |
| `sudo` | run as administrator (asks for your password) | `sudo reboot` |
| `python` | run a Python script | `python check_camera.py --show` |
| `bash` | run a shell script | `bash install_shortcuts.sh` |

## Keyboard tricks
- **Tab**: auto-completes file names. Type `hand_t` + Tab → `hand_to_braccio.py`. It saves typos.
- **↑ / ↓**: scroll through previous commands.
- **Ctrl+C**: stops the running program. Our scripts catch this and send the arm **home** first.
- **Ctrl+Shift+C / Ctrl+Shift+V**: copy and paste inside the terminal (plain Ctrl+C means "stop"!).

## Spaces in names, quotes and `*`
The shell splits commands at spaces. A name with a space, like `USB DEVICE`, must be quoted:
```bash
cp "/media/braccio/USB DEVICE/joint_test.py" ~/braccio-vision/
```
Or use the **wildcard** `*`, which means "anything". The shell replaces it with the real name, spaces included:
```bash
cp /media/braccio/*/joint_test.py ~/braccio-vision/
```
> [!warning] Common typos from this project
> - `rs-emumerate-devices` → **`rs-enumerate-devices`**
> - `cp"file"` → there must be a **space** after `cp`
> - `media/braccio/...` → missing the leading `/`, so the shell looks for a `media` folder *inside the current one*

## Command options (flags)
Words starting with `-` or `--` change what a command does:
```bash
python hand_to_braccio.py --show --arm-ip 192.168.1.100
#        script             flag    flag with a value
```
Each script lists its flags with `--help`:
```bash
python hand_to_braccio.py --help
```

## Virtual environments
A **venv** is a private folder of Python plus libraries, so this project's libraries can't break the system's Python. Ours is `~/braccio-venv`.

Two ways to use it:
```bash
# A) activate it, then plain "python" means the venv's python
source ~/braccio-venv/bin/activate
python check_camera.py
deactivate                       # leave it

# B) call the venv's python directly (no activation needed)
~/braccio-venv/bin/python ~/braccio-vision/check_camera.py
```
The desktop icon and the Control Panel use **B**.

## Permissions
- `sudo`: needed for system changes (installing with `apt`, editing `/boot/firmware/config.txt`, rebooting).
- `chmod +x file.sh`: makes a script executable, so `./file.sh` works. Otherwise use `bash file.sh`.

## Piping and redirecting (useful later)
```bash
python check_camera.py | grep FPS            # "|" sends the output into grep: show only FPS lines
python check_camera.py > camera_log.txt      # ">" saves the output to a file
```

Next: [[Terminal Commands Cheat Sheet]]
