#!/usr/bin/env bash
# Set the backlight thresholds for YOUR camera and panel. The shipped numbers
# came off the author's hardware and mean nothing on yours: overprint-light
# reports a 0-255 average, and what a "bright room" reads varies enormously
# between sensors.
set -euo pipefail
CONF="$HOME/.config/overprint/backlight.conf"
LIGHT="$HOME/.local/bin/overprint-light"
[[ -x $LIGHT ]] || { echo "overprint-light is not installed"; exit 1; }

read -r -p "Sit in the BRIGHTEST light you work in, then press Enter." _ </dev/tty
bright=$("$LIGHT" | cut -d' ' -f1); echo "  bright reads $bright"
read -r -p "Now make it as DARK as you work in, then press Enter." _ </dev/tty
dark=$("$LIGHT" | cut -d' ' -f1); echo "  dark reads $dark"

knee=$(python3 -c "print(max(20, round(float('$bright') * 1.05)))")
set_key() {
  if grep -qE "^[[:space:]]*$1[[:space:]]*=" "$CONF" 2>/dev/null; then
    sed -i -E "s|^[[:space:]]*$1[[:space:]]*=.*|$1=$2|" "$CONF"
  else printf '%s=%s\n' "$1" "$2" >> "$CONF"; fi
}
set_key BRIGHT_KNEE "$knee"
echo
echo "BRIGHT_KNEE=$knee written to $CONF"
echo "That is the reading at which the backlight reaches BRIGHT_MAX."
echo "If the screen ends up too dim in a bright room, lower it; too bright in a"
echo "dark one, raise BRIGHT_MIN. Apply with: overprint-appearance status"
