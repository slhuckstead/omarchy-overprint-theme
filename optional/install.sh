#!/usr/bin/env bash
# Install the optional parts of Overprint: the screensaver and the backlight
# adapter. The THEME itself needs none of this -- `omarchy theme install` is
# enough for that. Everything here is reversible with ./uninstall.sh.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
BIN="$HOME/.local/bin"
UNITS="$HOME/.config/systemd/user"
HOOKS="$HOME/.config/omarchy/hooks/theme-set.d"
UPDATE_HOOKS="$HOME/.config/omarchy/hooks/post-update.d"
MARK_BEGIN="# >>> overprint PATH >>>"
MARK_END="# <<< overprint PATH <<<"

WANT_SCREENSAVER=ask
WANT_BACKLIGHT=ask
for a in "$@"; do
  case $a in
    --screensaver)    WANT_SCREENSAVER=yes ;;
    --no-screensaver) WANT_SCREENSAVER=no ;;
    --backlight)      WANT_BACKLIGHT=yes ;;
    --no-backlight)   WANT_BACKLIGHT=no ;;
    --yes|-y)         WANT_SCREENSAVER=yes; WANT_BACKLIGHT=yes ;;
    -h|--help)
      sed -n '2,6p' "$0"; echo
      echo "  --screensaver / --no-screensaver   --backlight / --no-backlight   --yes"
      exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

ask() {                       # ask <question>  -> 0 for yes
  local reply
  read -r -p "$1 [y/N] " reply </dev/tty
  [[ ${reply,,} == y* ]]
}

need() { command -v "$1" >/dev/null || { echo "missing: $1"; return 1; }; }

echo "Overprint optional components"
echo

# ---------------------------------------------------------------- screensaver
if [[ $WANT_SCREENSAVER == ask ]]; then
  cat <<'EXPLAIN'
SCREENSAVER
  A drifting ink field in your theme's colours, five variations, one picked at
  random each time the screen sleeps.

  Installing it makes TWO changes outside ~/.local/bin, because Omarchy has no
  setting for a custom screensaver:

    1. ~/.bashrc gains a marked block that moves ~/.local/bin to the FRONT of
       PATH. Anything you put there will then shadow a system command of the
       same name. The block is fenced with markers and uninstall.sh removes it.

    2. ~/.local/bin/omarchy-launch-screensaver is generated from your installed
       copy of Omarchy's launcher, with the inner command pointed at this
       renderer. It shadows the packaged one. A post-update hook re-derives it
       from upstream's after every `omarchy update`, so it does not go stale.

  If neither is acceptable, answer no -- the theme is unaffected.

EXPLAIN
  ask "Install the screensaver?" && WANT_SCREENSAVER=yes || WANT_SCREENSAVER=no
fi

if [[ $WANT_SCREENSAVER == yes ]]; then
  need python3 || exit 1
  python3 -c 'import numpy' 2>/dev/null || { echo "screensaver needs python numpy"; exit 1; }
  mkdir -p "$BIN" "$HOOKS" "$UPDATE_HOOKS"
  install -m755 "$HERE"/bin/overprint-screensaver \
                "$HERE"/bin/overprint-screensaver-run \
                "$HERE"/bin/overprint-screensaver-plate \
                "$HERE"/bin/overprint-make-launcher-shadow "$BIN"/
  # Not screensaver-specific, but they belong on PATH and this is the only
  # install path the theme has.
  install -m755 "$HERE"/bin/overprint-make-preview "$HERE"/bin/overprint-colophon \
                "$HERE"/bin/overprint-repull "$BIN"/
  # Weekly re-pull of the current wallpaper. Installed, deliberately NOT enabled:
  #   systemctl --user enable --now overprint-repull.timer
  install -m644 "$HERE"/systemd/overprint-repull.service \
                "$HERE"/systemd/overprint-repull.timer "$UNITS"/
  mkdir -p "$UNITS"

  if ! grep -qF "$MARK_BEGIN" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" <<EOF

$MARK_BEGIN
# Omarchy's env-bootstrap APPENDS ~/.local/bin, which leaves /usr/share/omarchy/bin
# winning every name. A plain "add if missing" guard is a no-op here because the
# directory is already on PATH by this point -- so drop it and prepend.
PATH=\$(printf '%s' "\$PATH" | tr ':' '\n' | grep -vxF "\$HOME/.local/bin" | paste -sd:)
export PATH="\$HOME/.local/bin:\$PATH"
$MARK_END
EOF
    echo "  ~/.bashrc: added the PATH block"
  else
    echo "  ~/.bashrc: PATH block already present"
  fi

  "$BIN"/overprint-make-launcher-shadow
  install -m755 "$HERE"/hooks/theme-set.d/overprint-screensaver "$HOOKS"/
  # An Omarchy update ships a new packaged launcher, and the shadow built above
  # is then stale -- it keeps running whatever the OLD one said. That fails
  # silently: you simply get the stock ttfx wordmark back. This hook re-derives
  # the shadow after every `omarchy update`, and shouts if it cannot.
  install -m755 "$HERE"/hooks/post-update.d/overprint-launcher-shadow.hook "$UPDATE_HOOKS"/
  "$BIN"/overprint-screensaver-plate >/dev/null && echo "  wrote the fallback screensaver plate"
  echo "  screensaver installed. Test it with: omarchy-launch-screensaver force"
  echo "  (open a NEW shell first, so the PATH change is in effect)"
fi

# ------------------------------------------------------------------ backlight
if [[ $WANT_BACKLIGHT == ask ]]; then
  cat <<'EXPLAIN'

BACKLIGHT AND GROUND ADAPTER
  Ramps your backlight to match room light, sampled every 10 minutes. It can
  also switch the GROUND -- day (paper) / slate / night -- as the room or the
  day changes, keeping the composition of the wallpaper you are on.

  GROUND SWITCHING IS INSTALLED OFF and stays off until you turn it on. It has
  two sources you choose between: the room, via the camera, or the sun, which
  needs no camera at all. See `overprint-appearance ground`.

  If the machine has no ambient light sensor it uses the WEBCAM with exposure
  locked, and the LED will blink on each sample. It never writes an image
  anywhere -- only a single average brightness number -- but if a camera waking
  every ten minutes is not something you want, answer no. (Backlight off plus
  the solar ground source never opens the camera at all.)

  No light thresholds are shipped, because a 0-255 reading through a locked
  exposure means nothing on another camera. Measure yours:
    ./calibrate.sh                      the backlight knee, two button presses
    overprint-calibrate-ground --start   the ground thresholds, over a real day

EXPLAIN
  ask "Install the backlight adapter?" && WANT_BACKLIGHT=yes || WANT_BACKLIGHT=no
fi

if [[ $WANT_BACKLIGHT == yes ]]; then
  need brightnessctl || { echo "  install brightnessctl first"; exit 1; }
  need v4l2-ctl || echo "  note: v4l2-ctl (v4l-utils) missing; the camera path will not work"
  mkdir -p "$BIN" "$UNITS" "$HOME/.config/overprint"
  install -m755 "$HERE"/bin/overprint-light "$HERE"/bin/overprint-adapt \
                "$HERE"/bin/overprint-ground "$HERE"/bin/overprint-calibrate-ground \
                "$HERE"/bin/overprint-appearance "$HERE"/bin/overprint-notify-failure "$BIN"/
  install -m644 "$HERE"/systemd/overprint-backlight.timer \
                "$HERE"/systemd/overprint-backlight.service \
                "$HERE"/systemd/overprint-failure-notify@.service "$UNITS"/
  [[ -f $HOME/.config/overprint/backlight.conf ]] || cp "$HERE"/backlight.conf.example "$HOME/.config/overprint/backlight.conf"
  systemctl --user daemon-reload
  systemctl --user enable --now overprint-backlight.timer
  echo "  backlight adapter installed and running. Calibrate with ./calibrate.sh"
fi

echo
echo "Done. Uninstall with $HERE/uninstall.sh"
