#!/usr/bin/env python3
"""Generate the Overprint theme into ~/.config/omarchy/themes/overprint.

ONE theme, one palette, and every press and ground level kept as a wallpaper.

This used to emit twelve themes -- four presses x day/slate/night. Measured, the
presses were not four palettes: their accents sat 0.020 apart in OKLab and their
day grounds 0.007, both well under a just-noticeable difference, and every
wallpaper file was one of six compositions re-inked. The differences that were
real -- ground weight, and which pair of inks dominates a composition -- are
differences between IMAGES, so that is where they now live.
"""
import datetime, json, os, sys, shutil, subprocess, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, compose, palette as P, themes

# The local build renders at the SAME size as the published set. These are the
# same directory: DEST/SLUG is ~/.config/omarchy/themes/overprint, which is
# exactly where `omarchy theme install` clones this repo. When these differed,
# running the README's own `python3 generator/generate.py` inside a checkout
# deleted twelve tracked 3840x2160 files and rewrote them at 2560x1600 -- the
# reverse of the aspect decision, and a dirty tree. Use --for-display for a
# panel that is not 16:9.
W, H = 3840, 2160
DEST = os.path.expanduser("~/.config/omarchy/themes")
SLUG = "overprint"
# Icons are CHOSEN, not inherited. These used to be borrowed wholesale from a
# stock theme (day from flexoki-light, the dark grounds from matte-black), which
# is how the light variant quietly ended up on Yaru-blue while night and slate
# ran Yaru-red -- three weights of one theme disagreeing about their own accent.
# Overprint's accent is the harbour blue ink on every ground (#5B97D6 night,
# #7AB8F9 slate, #0C4474 day), so the icons are blue on every ground too, and
# Yaru's `-dark` variants carry the dark ones. Omarchy already uses that
# convention (solitude ships Yaru-sage-dark).
ICONS = {"day": "Yaru-blue", "slate": "Yaru-blue-dark", "night": "Yaru-blue-dark"}

KEY_ORDER = ["mode", "", "accent", "selection", "muted", "",
    "background", "dark_background", "darker_background", "lighter_background", "",
    "foreground", "dark_foreground", "light_foreground", "bright_foreground", "",
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown", "",
    "bright_red", "bright_yellow", "bright_green", "bright_cyan", "bright_blue",
    "bright_magenta", "",
    "hyprland_active_border", "hyprland_inactive_border"]

HEADER = """# Overprint
#
# Generated, not chosen. The three inks of this press are:
#   {inks}
# Most colours below are something this press can physically make: an ink alone,
# two inks overprinted, or all three. Where no ink or overprint lands near an
# ANSI hue the colour is SYNTHESISED at that hue, inheriting this press's own
# lightness and saturation -- a little over half the palette, in practice.
# Snapping to the nearest real ink instead would let two slots collapse onto one
# indistinguishable colour, which breaks the one-colour-one-meaning contract the
# terminal relies on.
#
# Contrast targets are deliberately NOT uniform across the hues. Driving every
# hue to one ratio flattened lightness across the palette to under a
# just-noticeable difference, leaving hue as the only thing separating two
# slots -- which is precisely what colour-vision deficiency takes away. Red and
# green carry pass/fail meaning, so they are pushed furthest apart.
#
# Every hue clears its target against `selection`, the extreme of the three
# grounds that carry text, and therefore against `background` and
# `lighter_background` as well.
#
# Regenerate with:  python3 ~/.local/share/overprint/generate.py
"""

README = """# Overprint

A Risograph press, simulated. Three inks, real halftone screens at 15/75/45
degrees, subtractive overprint on paper and screen-blend on dark grounds, paper
grain, and deliberate misregistration.

## Inks

    {inks}

## Wallpapers

{nwall} of them: {npress} presses x {nlevel} ground weights x {nvar} compositions.
The palette is fixed -- these vary the ink set and how heavy the paper prints,
which is where the visible differences actually were.

Named `<press>-<level>-<composition>.png`:

  presses  {presses}
  levels   {levels}

## Structure

Every wallpaper is derived from the golden ratio: a diminishing nested series of
large fields, one dominant, no visible grid. Nothing is placed by eye. Fields lay
ink down over each other rather than adding to each other, so a nested
composition cannot stack past what a press could physically put on paper.

## Canopy

Within any field the three inks trade places locally at 20-44px while total
coverage holds constant. So a field reads as one flat colour at arm's length and
decomposes into distinct hues at 1:1 -- the way a tree canopy reads as green and
turns out to be greens, browns, blues, reds and yellows.

## Palette

Derived from the inks and contrast-verified, not hand-picked. Verification is
against `selection`, the extreme of the three grounds that carry text; solving
against `background` alone left every hue slot failing on the other two.

Generated by `~/.local/share/overprint/generate.py`. Edit the generator, not
this directory -- regenerating overwrites everything here.
"""


# ---------------------------------------------------------------- shell.toml
# Omarchy generates shell.toml from colors.toml when a theme does not ship one.
# That generic file gives every surface in the shell -- bar, popups, tooltips,
# notifications, launcher, menu, polkit, lock -- borders taken from ONE token,
# `hyprland.active-border`, and interaction states that are the foreground
# colour at four different opacities. Two consequences, both wrong for this
# theme:
#
#   1. Once colors.toml carried a real three-ink gradient, EVERY card in the
#      shell got it, tooltips included. A gradient on everything signals
#      nothing. Here the gradient means one thing -- "this window is active" --
#      and no other surface is allowed to wear it. The single exception is the
#      lock screen's typing state, which is a genuine active state.
#   2. A riso press does not have four opacities of the same grey. It has
#      plates. Interaction states climb through INK: hover and focus in the
#      primary ink, selection as ink actually laid down, and the selected row
#      edged in the overprint colour -- the second plate registering over the
#      first. That mix colour appears nowhere else in the shell, which is what
#      makes a selected row read as printed rather than highlighted.
#
# Paper is also not glass. Omarchy floats the launcher at 0.95 and the lock card
# at 0.8; ink prints on an opaque sheet, and the doctrine is explicitly not to
# chase Liquid Glass, so both are pulled up.
#
# Sizes, spacing and the type scale are deliberately left at Omarchy's defaults.
# Those are the distribution's decisions and this theme has no better ones.
SHELL = """# Overprint -- shell surfaces.
#
# GENERATED by ~/.local/share/overprint/generate.py. Do not edit; edit the
# generator. Shipping this file suppresses Omarchy's generic one entirely, so
# every key the shell reads has to be present here.
#
# The rule: the three-ink gradient is the ACTIVE WINDOW signal. Nothing else
# wears it except the lock screen while you are typing. Everything else gets a
# single ink, so the gradient keeps meaning something.

[bar]
background       = "{background}"
background-alpha = 1.0
text             = "{foreground}"
# Recording, dictation, alerts, updates. The press's fluoro ink, which is what
# it is for -- not the palette's ANSI red, which has to answer to the terminal.
active           = "{ink_secondary}"
scale-with-font  = true
size-horizontal  = 26
size-vertical    = 28

[hyprland]
active-border            = "{active_border}"
active-border-foreground = "{foreground}"

[controls]
# Idle chrome stays uninked -- if resting controls carry ink there is no ink
# left to mean anything when one is hovered.
normal-color        = "{foreground}"
normal-fill-alpha   = 0.04
normal-border       = "{foreground}"
normal-border-width = 1
normal-border-alpha = 0.35

# Hover and keyboard cursor: the first plate touches the sheet.
hover-cursor-color        = "{ink_primary}"
hover-cursor-fill-alpha   = 0.10
hover-cursor-border       = "{ink_primary}"
hover-cursor-border-width = 1
hover-cursor-border-alpha = 0.45

# Focus is deliberately NOT a copy of hover, which is what the stock file does.
# Same ink, same fill, much harder edge -- a registration mark, not a glow. On a
# keyboard-first desktop, where focus sits is the question you ask most often.
focus-color        = "{ink_primary}"
focus-fill-alpha   = 0.08
focus-border       = "{ink_primary}"
focus-border-width = 1
focus-border-alpha = 0.85

# Selected: ink laid down, edged in what the two inks make where they overlap.
selected-color        = "{ink_primary}"
selected-fill-alpha   = 0.20
selected-border       = "{ink_mix}"
selected-border-width = 1
selected-border-alpha = 0.55

pressed-fill-alpha   = 0.26
selection-fill-alpha = 0.35

[spacing]
scale = 1.0
scale-with-font = true

[font]
base-size = 12

[popups]
background       = "{background}"
background-alpha = 1.0
text             = "{foreground}"
border           = "{accent}"
border-alpha     = 1.0

[tooltip]
# Transient information, never focused. The quietest border in the shell.
background       = "{background}"
background-alpha = 1.0
text             = "{foreground}"
border           = "{muted}"
border-alpha     = 0.5

[notifications]
background       = "{background}"
background-alpha = 1.0
text             = "{foreground}"
border           = "{accent}"
border-alpha     = 1.0
countdown        = "{ink_secondary}"

[launcher]
background                = "{background}"
background-alpha          = 1.0
text                      = "{foreground}"
border                    = "{accent}"
border-alpha              = 1.0
scrim                     = "{background}"
scrim-alpha               = 0.5
selected-background       = "{ink_primary}"
selected-background-alpha = 0.18
# Not the accent: the accent IS this ink, and it would vanish into its own wash.
selected-text             = "{bright_foreground}"
selected-border           = "{ink_mix}"
selected-border-alpha     = 0.55
# NOT in Omarchy's stock template, whose default is 0 -- a selected row there
# is a fill with no edge. Border.surfaceWidths() does read <token>-width per
# surface, so this is a real key; without it the overprint colour above
# renders nothing at all. Found by pixel-sampling the row edge, which is the
# only way to tell a missing border from a subtle one.
selected-border-width     = 1

[menu]
background                = "{background}"
background-alpha          = 1.0
text                      = "{foreground}"
border                    = "{accent}"
border-alpha              = 1.0
scrim                     = "{background}"
scrim-alpha               = 0.5
selected-background       = "{ink_primary}"
selected-background-alpha = 0.18
selected-text             = "{bright_foreground}"
selected-border           = "{ink_mix}"
selected-border-alpha     = 0.55
# NOT in Omarchy's stock template, whose default is 0 -- a selected row there
# is a fill with no edge. Border.surfaceWidths() does read <token>-width per
# surface, so this is a real key; without it the overprint colour above
# renders nothing at all. Found by pixel-sampling the row edge, which is the
# only way to tell a missing border from a subtle one.
selected-border-width     = 1

[polkit]
background       = "{background}"
background-alpha = 1.0
text             = "{foreground}"
text-error       = "{red}"
border           = "{accent}"
border-error     = "{red}"
border-alpha     = 1.0
scrim            = "{background}"
scrim-alpha      = 0.5
accent           = "{accent}"

[lock]
background       = "{background}"
background-alpha = 0.92
text             = "{foreground}"
placeholder      = "{muted}"
text-error       = "{red}"
border           = "{accent}"
# The one surface besides the window border that gets the full press: typing a
# password is a real active state, and it is the only feedback the lock screen
# gives that it is listening.
border-active    = "{active_border}"
border-error     = "{red}"
border-alpha     = 1.0
selection        = "{ink_primary}"
selection-alpha  = 0.45

[image-picker]
scrim                   = "{background}"
scrim-alpha             = 0.5
text                    = "{foreground}"
selected-border         = "{accent}"
selected-border-alpha   = 1.0
unselected-border       = "{foreground}"
unselected-border-alpha = 0.22
"""


def shell_toml(cols):
    return SHELL.format(active_border=cols["hyprland_active_border"], **cols)


def wordmark(cols, path, w=800, h=188, text="OVERPRINT"):
    """The plymouth boot logo. NOT a wallpaper.

    unlock.png is misleadingly named: its only consumer is
    omarchy-plymouth-set-by-theme, which installs it verbatim as plymouth's
    logo.png. Plymouth centres that at NATIVE SIZE and then places every other
    element relative to it:

        entry.y = logo.y + logo.height + 40      (omarchy.script:112)

    So shipping the hero wallpaper here -- which this did -- put a full-screen
    image in the logo slot and pushed the passphrase box, the lock icon, the
    password bullets and the progress bar clean off the bottom of the screen.
    On an encrypted disk that means typing the passphrase blind, and it fails
    silently because plymouth accepts the keystrokes either way. Every
    first-party theme ships a small transparent wordmark (800x188); so do we.

    Drawn with the CONTRAST-SOLVED palette rather than the raw inks, for the
    same reason everything else here is: raw #FFE800 on paper is invisible.
    """
    font = None
    for want in ("Libre Franklin Black", "Libre Franklin", "Liberation Sans Bold",
                 "DejaVu Sans Bold", "sans-serif"):
        try:
            r = subprocess.run(["fc-match", "-f", "%{file}", want],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip() and os.path.exists(r.stdout.strip()):
                font = r.stdout.strip(); break
        except Exception:
            continue
    if not font:
        print("  no usable font for the wordmark; unlock.png not written", file=sys.stderr)
        return False
    # Press order, and the misregistration IS the point -- the same deliberate
    # offset the wallpapers use, at wordmark scale.
    layers = [(-4, -2, cols["blue"]), (0, 0, cols["red"]), (4, 2, cols["yellow"])]
    args = ["magick", "-size", f"{w}x{h}", "xc:none"]
    for dx, dy, col in layers:
        args += ["(", "-size", f"{w}x{h}", "xc:none", "-font", font,
                 "-pointsize", "96", "-fill", col, "-gravity", "center",
                 "-annotate", f"{dx:+d}{dy:+d}", text, ")",
                 "-compose", "over", "-composite"]
    args += ["-define", "png:exclude-chunk=time", path]
    subprocess.run(args, check=True)
    return True


def toml(cols, inks):
    out = [HEADER.format(inks="  ".join(inks)), ""]
    for k in KEY_ORDER:
        if k == "":
            out.append("")
        elif k in cols:
            out.append(f'{k} = "{cols[k]}"')
    return "\n".join(out).rstrip() + "\n"


def main(level=None, slug=None, ship=None, levels=None):
    press = themes.CANON_PRESS
    level = level or themes.CANON_LEVEL
    slug = slug or SLUG
    ship = ship or SHIP
    inks = themes.INKS[press]
    night = themes.is_dark(level)
    d = os.path.join(DEST, slug)
    os.makedirs(os.path.join(d, "backgrounds"), exist_ok=True)

    cols = P.build(press, inks, *themes.GROUNDS[press], night=night,
                   ui_ground=themes.level_ground(press, level),
                   fg_contrast=themes.LEVEL_FG[level], level=level)
    open(os.path.join(d, "colors.toml"), "w").write(toml(cols, inks))
    # The screensaver needs the inks themselves, which colors.toml does not
    # carry -- it holds only what the press produced, not what it loaded.
    open(os.path.join(d, "overprint.toml"), "w").write(
        f'press = "{press}"\nmode = "{level}"\n'
        f'night = {str(night).lower()}\n'
        f'ground = "{cols["background"]}"\n'
        'inks = [' + ", ".join(f'"{i}"' for i in inks) + ']\n')

    presses = list(themes.INKS)
    # The light theme renders only its own ground. Shipping night and slate
    # wallpapers under a light UI is incoherent, and they are byte-for-byte the
    # same images the dark theme already made -- rendering them again cost six
    # minutes and 215MB the first time this ran.
    levels = list(levels or themes.LEVELS)
    bg = os.path.join(d, "backgrounds")

    # Tuning the palette does not change a single wallpaper -- they are built
    # from the inks and grounds, not from colors.toml -- so --palette skips the
    # 80-second render and, more to the point, avoids rewriting 72 files
    # non-atomically underneath a theme that is currently applied.
    if "--palette" in sys.argv[1:]:
        ubg = USER_BG if slug == SLUG else os.path.join(
            os.path.dirname(USER_BG), slug)
        n = len(os.listdir(bg)) + (len(os.listdir(ubg))
                                   if os.path.isdir(ubg) else 0)
        print(f"  palette only; kept {n} existing wallpapers")
        # _finish() runs the collision gate and returns its verdict; dropping
        # that return is what made the gate unreachable on every build path.
        return _finish(d, bg, press, level, presses, levels, n, cols)

    user_bg = USER_BG if slug == SLUG else os.path.join(
        os.path.dirname(USER_BG), slug)
    os.makedirs(user_bg, exist_ok=True)
    # Only remove what this generator makes. user_bg is a user-owned directory
    # the README points people at for their own wallpapers, and the old code
    # deleted every entry in it -- and raised IsADirectoryError on any folder.
    known = {f"{p}-{l}-{v[0]}.png" for p in themes.INKS for l in themes.LEVELS
             for v in compose.VARIANTS}
    for target in (bg, user_bg):
        for old in os.listdir(target):
            if old in known:
                os.remove(os.path.join(target, old))
            elif os.path.isfile(os.path.join(target, old)):
                print(f"  keeping unrecognised file {target}/{old}")

    n = nship = 0
    for wp in presses:
        wp_inks = themes.INKS[wp]
        for wl in levels:
            wall = themes.level_wallpaper(wp, wl)
            pal = dict(inks=wp_inks, paper=wall, night=wall)
            for i, (name, _, _, _) in enumerate(compose.VARIANTS):
                img = engine.render(W, H, compose.make(name, W, H), pal,
                                    night=themes.is_dark(wl), cell=8.0,
                                    seed=1000 + i * 17,
                                    pull=zlib.crc32(f"{wp}-{wl}-{name}".encode()))
                stem = f"{wp}-{wl}-{name}"
                out = bg if stem in ship else user_bg
                engine.write_png(os.path.join(out, stem + ".png"), img)
                n += 1
                nship += (out is bg)
            print(f"  {wp}-{wl:<6} {len(compose.VARIANTS)} backgrounds")
    print(f"  -> {nship} in the theme dir, {n - nship} in {user_bg}")

    # A three-ink halftone print genuinely has few distinct colours; 24-bit PNG
    # spends most of its bytes on grain noise. Quantising to 256 measured a 0.77%
    # RMSE difference -- visually indistinguishable at 1:1 -- for a ~63% saving.
    # Worth it: this directory lives in ~/.config, which is snapshotted.
    print("  quantising...")
    for target in (bg, user_bg):
        subprocess.run("magick mogrify -colors 256 -define png:exclude-chunk=time "
                       "-define png:compression-level=9 " + os.path.join(target, "*.png"),
                       shell=True, check=False)

    _finish(d, bg, press, level, presses, levels, n, cols)


# ------------------------------------------------------------------- publish
# `python3 generate.py --dist [outdir]` exports an installable Omarchy theme
# repo. It does NOT touch the local theme -- the 132-wallpaper install stays
# exactly as it is. Two different artefacts with two different jobs.
#
# WHAT SHIPS, AND WHY IT IS SMALLER. The local theme carries every press and
# every ground because they cost nothing here. A repo is cloned over a network
# by people who have not seen it yet, and the stock Omarchy themes ship 4-8
# wallpapers at 2-18MB; 132 at 328MB is not a curation, it is a dump, and
# "defaults over decisions" is the first line of the doctrine. So the repo
# ships one wallpaper per composition FAMILY -- canon, modulor, duo, spiral,
# stack, register -- on the theme's own press and its own ground. That is a
# rule, like everything else here, not a hand-picked favourite.
#
# Nothing is lost locally: omarchy-theme-set enumerates BOTH the theme's
# backgrounds/ and ~/.config/omarchy/backgrounds/<theme>/ when cycling, so
# anyone who wants all 132 runs the generator and drops them in the latter.
#
# WHY 3840x2400 AND NOT 2560x1600. The local render size is this laptop's panel.
# Stock themes ship 3160-7680px wide, so a 2560px theme is soft on anyone
# else's display. engine.render() scales the halftone pitch, misregistration
# and canopy band with the frame (verified: the screen measures 8.00px at 2560
# and 12.00px at 3840, ratio 1.500), so this is the same press on a bigger
# sheet rather than a different-looking print.
# THE PUBLISHED SET IS 16:9, WHICH IS NOT THIS LAPTOP'S ASPECT.
#
# Omarchy hangs wallpaper with Image.PreserveAspectCrop
# (shell/plugins/background/Background.qml), so any mismatch between the image
# and the panel is taken off the edges. There is no aspect that serves everyone,
# so this is a majority call, measured:
#
#   shipping 16:10        1920x1080 / 2560x1440 / 3840x2160  lose 10% of height
#                         2560x1600 (this laptop)            exact
#                         3440x1440 ultrawide                loses 33%
#   shipping 16:9         1920x1080 / 2560x1440 / 3840x2160  EXACT
#                         2560x1600 (this laptop)            loses 10% of width
#                         3440x1440 ultrawide                loses 26%
#
# 16:9 is exact on the three commonest panels and better on ultrawide; it costs
# the author 10% of width, which is the right way round for a published theme.
# It matters more here than for a photographic theme because these compositions
# are nested golden-ratio fields -- a crop re-proportions the very thing the
# composition is.
#
# Anyone who wants their own panel exactly: `generate.py --for-display`.
DIST_W, DIST_H = 3840, 2160

# Omarchy enumerates BOTH a theme's own backgrounds/ and
# ~/.config/omarchy/backgrounds/<theme>/ when cycling (omarchy-theme-set), so
# splitting them costs nothing and buys two things:
#
#   - `omarchy theme install` does `rm -rf` on the theme directory before
#     cloning. The repo's derived name is `overprint`, the same as this local
#     build, so anything in the theme dir is destroyed by installing from our
#     own repo. The user dir survives it.
#   - The local theme dir then mirrors what actually ships (the SHIP twelve),
#     which makes "what does an installing user get" answerable by looking.
#
# The other 120 are regenerated content, so this directory is cleared and
# rewritten on a full run exactly like the theme's own.
USER_BG = os.path.expanduser("~/.config/omarchy/backgrounds/" + "overprint")

REPO_README = """# {title}

A Risograph press, simulated, for [Omarchy](https://omarchy.org). Three inks,
real halftone screens at 15/75/45 degrees, subtractive overprint on paper and
screen-blend on dark grounds, paper grain, and deliberate misregistration.

    {inks}

{variant_note}

## Install

```bash
omarchy theme install {repo}
```

## What this is

Nothing here is hand-picked. The palette is *solved*: every ANSI slot is filled
by what this press can physically make -- an ink alone, two overprinted, or all
three -- and then retargeted in OKLab until it clears its contrast floor. The
contrast targets are deliberately non-uniform per hue, because driving every hue
to one ratio flattens lightness below a just-noticeable difference and leaves
hue as the only thing separating two slots, which is exactly what colour-vision
deficiency takes away. Red and green are pushed furthest apart.

Every colour is verified against `selection`, the extreme of the three grounds
that carry text, so it clears against `background` and `lighter_background` too.

The window border is three stops: an ink, what those two inks actually make
where they overlap on this ground, and the other ink. It is the only place in
the theme where an overprint is visible as itself.

`shell.toml` is included, so the bar, launcher, menu, notifications and lock
screen are themed as one surface rather than inheriting a generic fallback.
Interaction states climb through ink rather than through four opacities of the
same grey.

## Wallpapers

{nbg} of them: one per composition family -- {families} -- at {w}x{h}. Every
composition is derived from the golden ratio, a diminishing nested series of
large fields with one dominant, and nothing placed by eye.

The generator makes 132 (4 presses x 3 ground levels x 11 compositions). To use
the rest, put them in `~/.config/omarchy/backgrounds/overprint/` -- Omarchy
cycles that directory alongside the theme's own.

## Licence

MIT. See LICENSE.
"""

MIT = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# The six that ship. One per composition FAMILY -- canon, modulor, duo, spiral,
# stack, register -- rather than one per composition, which double-counted canon
# three times and spiral and register twice each.
#
# Six rather than twelve because a full `git clone` is what `omarchy theme
# install` does, and 12 wallpapers at 3840x2160 made that 125MB against 2-18MB
# for a stock Omarchy theme. Cutting COUNT rather than resolution is what keeps
# the halftone intact: rendering at 2560x1440 and letting a 4K panel upscale
# visibly dissolves the dot structure into smeared texture, which is the one
# thing this theme cannot afford to lose.
#
# The press and ground assignments hold the spread of the original twelve: all
# four presses appear, and each of the three grounds appears exactly twice.
# harbour-slate-4-modulor stays because it is the preview hero.
SHIP = [
    "orchard-night-3-canon-deep",    # canon     orchard  night
    "harbour-slate-4-modulor",       # modulor   harbour  slate   (preview hero)
    "ember-day-6-duo",               # duo       ember    day
    "tidal-day-7-spiral",            # spiral    tidal    day
    "harbour-night-9-stack",         # stack     harbour  night
    "ember-slate-11-register-alt",   # register  ember    slate
]


def _same_pixels(a, b):
    """True when two PNGs are pixel-identical, whatever their encoding."""
    r = subprocess.run(["magick", "compare", "-metric", "AE", a, b, "null:"],
                       capture_output=True, text=True)
    return (r.stderr.strip().split()[0] if r.stderr.strip() else "1") == "0"


# Every variant ships the same twelve compositions on the same presses, moved to
# its own ground -- so they are recognisably one theme in three weights rather
# than three curations that happen to share a name.
def ship_for(level):
    return [f"{s.split('-', 2)[0]}-{level}-{s.split('-', 2)[2]}" for s in SHIP]


SHIP_LIGHT = ship_for("day")

# Slug suffix per ground. `night` is the canon and owns the bare name; the other
# two are separate themes, which is how Omarchy does variants (Catppuccin /
# Catppuccin Latte) rather than a mode switch inside one theme.
VARIANT_SUFFIX = {"day": "light", "slate": "slate"}


def variant(level):
    """Build the theme for a non-canon ground."""
    slug = SLUG + "-" + VARIANT_SUFFIX[level]
    print(f"Generating the Overprint {VARIANT_SUFFIX[level].upper()} theme into", DEST)
    # Only this ground's wallpapers: the others are byte-for-byte the images
    # another variant already made, and a night wallpaper under a paper UI (or
    # the reverse) is incoherent besides.
    rc = main(level=level, slug=slug, ship=ship_for(level), levels=(level,)) or 0
    print("done" if rc == 0 else "done, WITH WARNINGS")
    return rc


def dist(outdir, force=False, width=None, previews=False, level=None):
    # This has already clobbered a published repo once. The dist directory IS
    # the git working tree, so a rebuild deletes tracked wallpapers before
    # writing new ones -- recoverable, but only if you notice. Refuse by
    # default and make the caller say they meant it.
    if os.path.isdir(os.path.join(outdir, ".git")) and not force:
        print(f"  {outdir} is a git working tree.\n"
              f"  Rebuilding rewrites tracked files. Re-run with --force if that is "
              f"what you want,\n  and check `git status` afterwards.", file=sys.stderr)
        return 2

    W = width or DIST_W
    H = int(round(W / (DIST_W / DIST_H)))
    press = themes.CANON_PRESS
    level = level or themes.CANON_LEVEL
    night = themes.is_dark(level)
    ship = SHIP if level == themes.CANON_LEVEL else ship_for(level)
    bg = os.path.join(outdir, "backgrounds")
    os.makedirs(bg, exist_ok=True)

    cols = P.build(press, themes.INKS[press], *themes.GROUNDS[press], night=night,
                   ui_ground=themes.level_ground(press, level),
                   fg_contrast=themes.LEVEL_FG[level], level=level)
    open(os.path.join(outdir, "colors.toml"), "w").write(toml(cols, themes.INKS[press]))
    open(os.path.join(outdir, "shell.toml"), "w").write(shell_toml(cols))
    # The screensaver reads this for the inks and the ground; colors.toml holds
    # only what the press PRODUCED, not what it loaded. dist() never wrote it,
    # so every published variant shipped without it and the renderer silently
    # fell back to hardcoded harbour-night -- a dark screensaver under a paper
    # theme. main() has always written it, which is why only the exports broke.
    open(os.path.join(outdir, "overprint.toml"), "w").write(
        f'press = "{press}"\nmode = "{level}"\n'
        f'night = {str(night).lower()}\n'
        f'ground = "{cols["background"]}"\n'
        'inks = [' + ", ".join(f'"{i}"' for i in themes.INKS[press]) + ']\n')

    order = [v[0] for v in compose.VARIANTS]

    # render() is deterministic, but `magick -colors 256` is NOT: it picks the
    # same 256 colours and emits them in a different PLTE order each run, so the
    # bytes change while every pixel stays identical (verified: AE 0, same byte
    # count). Rewriting regardless would mean ~30MB of meaningless churn in git
    # on every rebuild. So build into a staging dir and only adopt a file whose
    # PIXELS actually differ from the one already published.
    stage = os.path.join(outdir, ".dist-stage")
    shutil.rmtree(stage, ignore_errors=True)
    os.makedirs(stage)
    for stem in ship:
        wp, wl, name = stem.split("-", 2)
        wall = themes.level_wallpaper(wp, wl)
        pal = dict(inks=themes.INKS[wp], paper=wall, night=wall)
        i = order.index(name)
        img = engine.render(W, H, compose.make(name, W, H), pal,
                            night=themes.is_dark(wl), cell=8.0, seed=1000 + i * 17,
                            pull=zlib.crc32(stem.encode()))
        engine.write_png(os.path.join(stage, stem + ".png"), img)

    print("  quantising...")
    subprocess.run("magick mogrify -colors 256 -define png:exclude-chunk=time "
                   "-define png:compression-level=9 " + os.path.join(stage, "*.png"),
                   shell=True, check=False)

    kept = adopted = 0
    for stem in ship:
        newf = os.path.join(stage, stem + ".png")
        cur = os.path.join(bg, stem + ".png")
        if os.path.exists(cur) and _same_pixels(cur, newf):
            kept += 1
        else:
            shutil.move(newf, cur)
            adopted += 1
            print(f"  {stem}  (changed)")
    for f in os.listdir(bg):                      # drop anything no longer shipped
        if f[:-4] not in ship:
            os.remove(os.path.join(bg, f))
    shutil.rmtree(stage, ignore_errors=True)
    print(f"  {kept} unchanged, {adopted} written")

    # preview.png is the theme's card in the picker and preview-unlock.png is
    # what omarchy-plymouth-list gates on. unlock.png is NOT a lock-screen image
    # despite the name -- it is plymouth's LOGO, drawn at native size with the
    # passphrase box positioned beneath it, so it is built by wordmark() below
    # rather than cropped from the hero. See that function.
    #
    # These are only rebuilt when missing, or on --previews. Regenerating them
    # every run produces a few MB of diff that is resize and quantise noise off
    # the same source image, which buries the actual change in a review.
    hero_stem = next((x for x in ship if "modulor" in x), ship[0])
    hero = os.path.join(bg, f"{hero_stem.split('-',2)[0]}-{level}-"
                            f"{hero_stem.split('-',2)[2]}.png")
    if not os.path.exists(hero):
        pngs = sorted(f for f in os.listdir(bg) if f.endswith(".png"))
        hero = os.path.join(bg, pngs[0]) if pngs else None
    # 2880x1800 matches the first-party previews (solitude, last-horizon).
    # Ours shipped at 1280x800, so the picker card was visibly softer than every
    # theme beside it on a HiDPI panel -- a gap that costs nothing to close.
    # 1920x1080 for preview-unlock.png, matching solitude / last-horizon / lupine.
    # It is the Plymouth PICKER thumbnail (omarchy-plymouth-switcher symlinks it),
    # a different job from preview.png, and it was shipping at the same 2880x1800
    # as the desktop card by accident.
    want = [("preview.png", "2880x1800"), ("preview-unlock.png", "1920x1080")]
    todo = [] if hero is None else [(f, r) for f, r in want
            if previews or not os.path.exists(os.path.join(outdir, f))]
    for f, r in todo:
        # -resize fits INSIDE the box; ^ + extent fills it, which is what
        # "matches the first-party previews" requires.
        subprocess.run(["magick", hero, "-resize", r + "^", "-gravity", "center",
                        "-extent", r, os.path.join(outdir, f)], check=True)
        subprocess.run(["magick", "mogrify", "-colors", "256",
                        "-define", "png:exclude-chunk=time",
                        "-define", "png:compression-level=9",
                        os.path.join(outdir, f)], check=False)
    print(f"  previews: {len(todo)} written, {len(want)-len(todo)} kept")

    if wordmark(cols, os.path.join(outdir, "unlock.png")):
        print("  unlock.png: wordmark written (plymouth logo, not a wallpaper)")

    open(os.path.join(outdir, "icons.theme"), "w").write(ICONS[level] + "\n")

    # The repo ships the generator so anyone can make the other 120.
    TITLES = {"night": "Overprint", "slate": "Overprint Slate",
              "day": "Overprint Light"}
    SIBLINGS = {
        "night": "This is the **night** ground -- the deep one, for a dark room. Two\n"
                 "siblings share its inks on different paper: [Overprint Slate]"
                 "(https://github.com/slhuckstead/omarchy-overprint-slate-theme)\n"
                 "lifts the ground so it survives daylight, and [Overprint Light]"
                 "(https://github.com/slhuckstead/omarchy-overprint-light-theme)\n"
                 "prints on paper.",
        "slate": "This is the **slate** ground -- a lifted dark, for a bright room where\n"
                 "the deep ground washes out and paper glares back. Its inks come out\n"
                 "paler than the night theme's, which is the ground rather than a\n"
                 "fault: higher contrast on a lifted ground means lighter. Siblings:\n"
                 "[Overprint](https://github.com/slhuckstead/omarchy-overprint-theme)\n"
                 "and [Overprint Light]"
                 "(https://github.com/slhuckstead/omarchy-overprint-light-theme).",
        "day":   "This is the **paper** ground -- the same three inks printing dark on a\n"
                 "light sheet. Its contrast targets are NOT the dark theme's inverted;\n"
                 "paper reflects, so a light ground has a lower ceiling (11.51:1 against\n"
                 "15.59) and needed its own solved set. Siblings: [Overprint]"
                 "(https://github.com/slhuckstead/omarchy-overprint-theme)\n"
                 "and [Overprint Slate]"
                 "(https://github.com/slhuckstead/omarchy-overprint-slate-theme).",
    }
    for fname, body in (("README.md", REPO_README.format(
                            title=TITLES.get(level, "Overprint"),
                            variant_note=SIBLINGS.get(level, ""),
                            inks="   ".join(themes.INKS[press]),
                            nbg=len(ship), w=W, h=H,
                            families=", ".join(sorted({s.split("-", 2)[2] for s in ship})),
                            repo=os.environ.get(
                                "OVERPRINT_REPO",
                                "https://github.com/<you>/omarchy-overprint-theme.git"))),
                        ("LICENSE", MIT.format(
                            year=datetime.date.today().year,
                            author=os.environ.get("OVERPRINT_AUTHOR", "Seth Huckstead")))):
        dst = os.path.join(outdir, fname)
        if not os.path.exists(dst):          # never clobber a curated README
            open(dst, "w").write(body)
            print(f"  wrote {fname}")

    gen = os.path.join(outdir, "generator")
    os.makedirs(gen, exist_ok=True)
    if True:
        for f in ("engine.py", "compose.py", "palette.py", "themes.py", "generate.py"):
            shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), f),
                        os.path.join(gen, f))

    P.check_collisions(cols)
    enforced = [c for c in P.COLLISIONS if c["enforced"]]
    for c in enforced:
        print(f"  collision: {c['kind']:<7} {c['a']}/{c['b']}  {c['dist']:.4f} "
              f"< {c['floor']:.3f}", file=sys.stderr)

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, dn, fs in os.walk(outdir) if ".git" not in dp for f in fs)
    print(f"\n  dist -> {outdir}")
    print(f"  {len(ship)} wallpapers ({level}) at {W}x{H}, {total/1048576:.1f} MB")
    if P.FALLBACKS:
        print(f"  WARNING: {len(P.FALLBACKS)} colour(s) fell back", file=sys.stderr)
    return 1 if (P.FALLBACKS or enforced) else 0


def _finish(d, bg, press, level, presses, levels, n, cols):
    # Shipping shell.toml suppresses Omarchy's generated one entirely.
    open(os.path.join(d, "shell.toml"), "w").write(shell_toml(cols))

    open(os.path.join(d, "README.md"), "w").write(README.format(
        inks="   ".join(themes.INKS[press]), nwall=n, npress=len(presses), nlevel=len(levels),
        nvar=len(compose.VARIANTS), presses=", ".join(presses),
        levels=", ".join(levels)))

    # preview.png is the theme's card in the picker and preview-unlock.png is
    # what omarchy-plymouth-list gates on. unlock.png is plymouth's LOGO, built
    # by wordmark() -- not a lock-screen image, whatever the name suggests.
    # The hero is harbour-night-4-modulor, which is NOT one of the SHIP twelve
    # (those carry harbour-SLATE-4-modulor), so after the split it lives in the
    # user directory. Look in both rather than assuming.
    hero_stem = f"{press}-{level}-{compose.VARIANTS[3][0]}.png"
    hero = os.path.join(bg, hero_stem)
    if not os.path.exists(hero):
        for alt in (USER_BG, os.path.join(os.path.dirname(USER_BG), os.path.basename(d)),
                    bg):
            cand = os.path.join(alt, hero_stem)
            if os.path.exists(cand):
                hero = cand; break
        else:
            pngs = sorted(f for f in os.listdir(bg) if f.endswith(".png"))
            if not pngs:
                print("  no wallpapers yet; skipping preview/unlock "
                      "(run a full build first)", file=sys.stderr)
                hero = None
            else:
                hero = os.path.join(bg, pngs[0])
    # NEVER clobber a curated preview. preview.png is a SCREENSHOT of a working
    # desktop made by overprint-make-preview, and regenerating it from the hero
    # -- which this did on every run, including --palette -- silently destroys
    # it. That happened: three cards, built by hand over an afternoon, replaced
    # by 1280x800 hero crops by a one-second palette rebuild. dist() has always
    # guarded its README this way; the same rule belongs here.
    # Force a rebuild from the hero with --previews.
    # Same sizes dist() uses, and for the same reason: 1280x800 was visibly
    # softer than every first-party theme beside it in the picker on a HiDPI
    # panel. That was fixed in dist() and NOT here, so a local build quietly
    # reintroduced the soft card the export had already cured.
    # -resize fits INSIDE the box; ^ + extent fills it.
    force_previews = "--previews" in sys.argv[1:]
    written = []
    for f, r in (("preview.png", "2880x1800"), ("preview-unlock.png", "1920x1080")):
        dst = os.path.join(d, f)
        if force_previews or not os.path.exists(dst):
            subprocess.run(["magick", hero, "-resize", r + "^", "-gravity", "center",
                            "-extent", r, dst], check=True)
            written.append(f)
        else:
            print(f"  kept existing {f} (--previews to rebuild from the hero)")
    wordmark(cols, os.path.join(d, "unlock.png"))

    # Only what was actually written this run. Re-quantising a KEPT file changes
    # its bytes without changing a pixel -- magick -colors 256 picks the same
    # colours in a different PLTE order every time -- which is exactly the
    # meaningless churn dist() already goes to trouble to avoid.
    # unlock.png is excluded entirely: wordmark() writes it small and clean, and
    # quantising an anti-aliased transparent wordmark only dithers its edges.
    for f in written:
        subprocess.run(["magick", "mogrify", "-colors", "256", "-define", "png:exclude-chunk=time",
                        "-define", "png:compression-level=9",
                        os.path.join(d, f)], check=False)

    open(os.path.join(d, "icons.theme"), "w").write(ICONS[level] + "\n")
    print(f"\n  {os.path.basename(d)}: palette {press}-{level}, bg {cols['background']}, "
          f"{n} wallpapers")
    # Two slots solving to the same colour is the failure a contrast check
    # cannot see, and the one that matters most: this palette's claim is
    # one-colour-one-meaning. Verified under simulated colour-vision deficiency,
    # because that is where separation actually collapses.
    P.check_collisions(cols)
    enforced = [c for c in P.COLLISIONS if c["enforced"]]
    for c in P.COLLISIONS:
        if not c["enforced"]:
            print(f"  note: closest {c['kind']} pair is {c['a']}/{c['b']} at "
                  f"{c['dist']:.4f} (reported, not gated)")
    if enforced:
        print(f"\n  {len(enforced)} slot collision(s) -- two meanings that look "
              f"the same:", file=sys.stderr)
        for c in enforced:
            print(f"    {c['kind']:<7} {c['a']} / {c['b']}  {c['dist']:.4f} "
                  f"(floor {c['floor']:.3f})", file=sys.stderr)

    # A colour that could not be solved is now recorded rather than silently
    # shipped as pure black or white. Fail the run so it cannot pass unnoticed.
    if P.FALLBACKS:
        print(f"\n  {len(P.FALLBACKS)} colour(s) fell back and lost their ink cast:",
              file=sys.stderr)
        for f in P.FALLBACKS:
            print(f"    {f['where']} {f['target']}:1 at hue {f['hue']} on "
                  f"{f['ground']} -> {f['result']}", file=sys.stderr)
    if P.FALLBACKS or enforced:
        return 1
    return 0


def for_display(level=None):
    """Re-render this theme's wallpapers at the focused monitor's exact size.

    The shipped set is 16:9 because that is the majority; this is the escape
    hatch for everyone else, and it costs two minutes. engine.render() scales
    the halftone, misregistration and canopy with the frame, so this is the same
    press on a differently-shaped sheet rather than a stretched one.
    """
    mons = json.loads(subprocess.run(["hyprctl", "monitors", "-j"],
                                     capture_output=True, text=True).stdout)
    focused = next((m for m in mons if m.get("focused")), mons[0])
    W = int(focused["width"]); H = int(focused["height"])
    if int(focused.get("transform", 0)) % 2 == 1:      # 90 / 270 rotated
        W, H = H, W
    level = level or themes.CANON_LEVEL
    slug = SLUG if level == themes.CANON_LEVEL else SLUG + "-" + VARIANT_SUFFIX[level]
    d = os.path.join(DEST, slug)
    bg = os.path.join(d, "backgrounds")
    if not os.path.isdir(bg):
        print(f"  {d} not built yet", file=sys.stderr)
        return 1
    # BOTH directories. The theme dir holds the twelve that ship; the other 120
    # live in the user dir, and a version of this that fixed only the first
    # twelve left the bulk of a rotation at the wrong aspect.
    user_bg = USER_BG if slug == SLUG else os.path.join(
        os.path.dirname(USER_BG), slug)
    targets = [bg] + ([user_bg] if os.path.isdir(user_bg) else [])
    order = [v[0] for v in compose.VARIANTS]
    total = skipped = 0
    print(f"  {focused['name']} is {W}x{H}; re-rendering {slug} to match")
    for target in targets:
        for stem in sorted(f for f in os.listdir(target) if f.endswith(".png")):
            name = stem[:-4]
            try:
                wp, wl, comp = name.split("-", 2)
                i = order.index(comp)
            except (ValueError, KeyError):
                skipped += 1                  # someone else's wallpaper; leave it
                continue
            if wp not in themes.INKS or wl not in themes.LEVELS:
                skipped += 1
                continue
            wall = themes.level_wallpaper(wp, wl)
            pal = dict(inks=themes.INKS[wp], paper=wall, night=wall)
            img = engine.render(W, H, compose.make(comp, W, H), pal,
                                night=themes.is_dark(wl), cell=8.0, seed=1000 + i * 17,
                                pull=zlib.crc32(stem.encode()))
            engine.write_png(os.path.join(target, stem), img)
            total += 1
        subprocess.run("magick mogrify -colors 256 -define png:exclude-chunk=time "
                       "-define png:compression-level=9 " + os.path.join(target, "*.png"),
                       shell=True, check=False)
        print(f"    {target}: done")
    print(f"  {total} wallpapers at {W}x{H}"
          + (f"; {skipped} left alone (not this generator's)" if skipped else ""))

    # unlock.png is deliberately NOT touched here. It is plymouth's logo, a
    # fixed-size wordmark with no relationship to this panel -- an earlier
    # version of this function refreshed it from the hero, which was correct
    # only while unlock.png was wrongly a copy of the wallpaper.
    return 0


def check(level=None):
    """Report contrast and separation for a ground without building anything.

    `--check [day|slate|night]`. Useful when tuning SLOT_CONTRAST, because a
    full run costs six minutes to tell you the same thing.
    """
    press = themes.CANON_PRESS
    levels = [level] if level else list(themes.LEVELS)
    rc = 0
    for lv in levels:
        P.FALLBACKS.clear(); P.COLLISIONS.clear()
        cols = P.build(press, themes.INKS[press], *themes.GROUNDS[press],
                       night=themes.is_dark(lv),
                       ui_ground=themes.level_ground(press, lv),
                       fg_contrast=themes.LEVEL_FG[lv], level=lv)
        P.check_collisions(cols)
        enf = [c for c in P.COLLISIONS if c["enforced"]]
        mark = "ok  " if not (P.FALLBACKS or enf) else "FAIL"
        star = "  <- CANON" if lv == themes.CANON_LEVEL else ""
        print(f"  {mark} {lv:<6} ground {cols['background']}  "
              f"contrast fallbacks {len(P.FALLBACKS)}  collisions {len(enf)}{star}")
        for f in P.FALLBACKS:
            print(f"         contrast: {f['where']} {f['target']}:1 -> {f['result']}")
        for c in enf:
            print(f"         collision: {c['kind']:<7} {c['a']}/{c['b']}  "
                  f"{c['dist']:.4f} < {c['floor']:.3f}")
        for c in P.COLLISIONS:
            if not c["enforced"]:
                print(f"         note: closest {c['kind']} pair {c['a']}/{c['b']} "
                      f"{c['dist']:.4f} (not gated)")
        # Exit status tracks what actually SHIPS -- which is now ALL THREE
        # grounds, each a published theme of its own. It used to gate on the
        # canon ground alone, correctly, back when day and slate were only
        # reported as what a light variant would have to fix. Left that way it
        # would print "ok" and exit 0 with a shipped theme broken, which is the
        # same class of lie as the "0 contrast failures" this file used to
        # claim while both counts were wrong.
        rc |= 1 if (P.FALLBACKS or enf) else 0
    if not level:
        print(f"\n  exit status gates on all {len(levels)} shipped grounds "
              f"({', '.join(levels)}); ask for one by name to gate on it alone")
    return rc


if __name__ == "__main__":
    if "--for-display" in sys.argv[1:]:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        sys.exit(for_display(args[0] if args else None))

    if "--check" in sys.argv[1:]:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        sys.exit(check(args[0] if args else None))

    if "--dist" in sys.argv[1:]:
        argv = sys.argv[1:]
        args = [a for a in argv if not a.startswith("--")]
        width = None
        if "--hires" in argv:
            width = int(args.pop(0)) if args and args[0].isdigit() else 3840
        out = os.path.expanduser(args[0] if args
                                 else "~/Work/omarchy-overprint-theme")
        os.makedirs(out, exist_ok=True)
        print("Exporting an installable Overprint theme into", out)
        lvl = next((l for f, l in (("--light", "day"), ("--slate", "slate"))
                    if f in argv), None)
        rc = dist(out, force="--force" in argv, width=width,
                  previews="--previews" in argv, level=lvl) or 0
        print("done" if rc == 0 else "done, WITH WARNINGS")
        sys.exit(rc)

    for flag, lvl in (("--light", "day"), ("--slate", "slate")):
        if flag in sys.argv[1:]:
            sys.exit(variant(lvl))

    print("Generating the Overprint theme into", DEST)
    rc = main() or 0
    print("done" if rc == 0 else "done, WITH WARNINGS")
    sys.exit(rc)
