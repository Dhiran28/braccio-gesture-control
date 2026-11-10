#!/usr/bin/env bash
# Creates ONE desktop icon, "Braccio Control Panel", that opens a window with all modes.
set -e
V="$HOME/braccio-vision"
D="$HOME/Desktop"
mkdir -p "$D"
chmod +x "$V"/launch/*.sh 2>/dev/null || true
python3 -c "import tkinter" 2>/dev/null || { echo "Installing tkinter (window library)..."; sudo apt install -y python3-tk; }
rm -f "$D"/braccio-*.desktop                      # remove older separate icons if present
cat > "$D/braccio-control-panel.desktop" <<EOD
[Desktop Entry]
Type=Application
Name=Braccio Control Panel
Comment=Start LIVE / Simulation / Arm check / Camera test
Exec=$HOME/braccio-venv/bin/python $V/control_panel.py
Icon=input-gaming
Terminal=false
EOD
chmod +x "$D/braccio-control-panel.desktop"
gio set "$D/braccio-control-panel.desktop" metadata::trusted true 2>/dev/null || true
# double-click runs it without the "Execute / Open" question
CONF="$HOME/.config/libfm/libfm.conf"
mkdir -p "$(dirname "$CONF")"
if [ -f "$CONF" ] && grep -q "quick_exec" "$CONF"; then
  sed -i 's/^quick_exec=.*/quick_exec=1/' "$CONF"
elif [ -f "$CONF" ] && grep -q "^\[config\]" "$CONF"; then
  sed -i '/^\[config\]/a quick_exec=1' "$CONF"
else
  printf "[config]\nquick_exec=1\n" >> "$CONF"
fi
echo "Created: $D/braccio-control-panel.desktop"
echo "Double-click 'Braccio Control Panel' on the desktop. If it doesn't show yet, reboot."
