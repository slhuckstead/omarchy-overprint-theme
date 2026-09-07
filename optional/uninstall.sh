#!/usr/bin/env bash
# Remove everything ./install.sh added. The theme is untouched.
set -uo pipefail
BIN="$HOME/.local/bin"; UNITS="$HOME/.config/systemd/user"
HOOKS="$HOME/.config/omarchy/hooks/theme-set.d"
UPDATE_HOOKS="$HOME/.config/omarchy/hooks/post-update.d"
MARK_BEGIN="# >>> overprint PATH >>>"; MARK_END="# <<< overprint PATH <<<"

systemctl --user disable --now overprint-backlight.timer 2>/dev/null
systemctl --user disable --now overprint-repull.timer 2>/dev/null
rm -f "$UNITS"/overprint-repull.{timer,service}
rm -f "$UNITS"/overprint-backlight.{timer,service} "$UNITS"/overprint-failure-notify@.service
systemctl --user daemon-reload 2>/dev/null

rm -f "$BIN"/overprint-{screensaver,screensaver-run,screensaver-plate,make-launcher-shadow} \
      "$BIN"/overprint-make-preview "$BIN"/overprint-colophon "$BIN"/overprint-repull \
      "$BIN"/overprint-{light,adapt,appearance,notify-failure} \
      "$BIN"/overprint-{ground,calibrate-ground} \
      "$BIN"/omarchy-launch-screensaver \
      "$HOOKS"/overprint-screensaver \
      "$UPDATE_HOOKS"/overprint-launcher-shadow.hook

# Hand the screensaver plate back to the packaged default.
if [[ -f /etc/skel/.config/omarchy/branding/screensaver.txt ]]; then
  cp -f /etc/skel/.config/omarchy/branding/screensaver.txt \
        "$HOME/.config/omarchy/branding/screensaver.txt" 2>/dev/null
fi

if grep -qF "$MARK_BEGIN" "$HOME/.bashrc" 2>/dev/null; then
  tmp=$(mktemp)
  awk -v b="$MARK_BEGIN" -v e="$MARK_END" '
    index($0,b){skip=1} !skip{print} index($0,e){skip=0}' "$HOME/.bashrc" > "$tmp"
  mv "$tmp" "$HOME/.bashrc"
  echo "removed the PATH block from ~/.bashrc"
fi

echo "Removed. Your config at ~/.config/overprint was left alone; delete it if you want."
