"""Derive a full 16-colour terminal palette from three printing inks.

Nothing is hand-picked. The candidate colours are exactly what the press can
make: each ink alone, each pair overprinted, all three overprinted, and tints of
each on paper. Every ANSI slot is filled by the candidate nearest that slot's
hue, then its lightness is retargeted in OKLab until it clears WCAG against the
ground -- reducing chroma only when lightness alone cannot get there.
"""
import math, sys, numpy as np

# ------------------------------------------------------------ colour space
def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float) / 255.0

def rgb2hex(c):
    c = np.clip(c, 0, 1)
    return "#" + "".join(f"{int(round(v*255)):02X}" for v in c)

def s2lin(c): return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
def lin2s(c): return np.where(c <= 0.0031308, c*12.92, 1.055*np.clip(c,0,None)**(1/2.4)-0.055)

_M1 = np.array([[0.4122214708,0.5363325363,0.0514459929],
                [0.2119034982,0.6806995451,0.1073969566],
                [0.0883024619,0.2817188376,0.6299787005]])
_M2 = np.array([[0.2104542553,0.7936177850,-0.0040720468],
                [1.9779984951,-2.4285922050,0.4505937099],
                [0.0259040371,0.7827717662,-0.8086757660]])

def rgb2oklab(c):
    lms = _M1 @ s2lin(np.asarray(c, float))
    return _M2 @ np.cbrt(lms)

def oklab2rgb(lab):
    lms = (np.linalg.inv(_M2) @ np.asarray(lab, float)) ** 3
    return lin2s(np.linalg.inv(_M1) @ lms)

def lab2lch(lab):
    L, a, b = lab
    return np.array([L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360])

def lch2lab(lch):
    L, C, H = lch
    r = math.radians(H)
    return np.array([L, C*math.cos(r), C*math.sin(r)])

# ---------------------------------------------------------------- contrast
def rel_lum(c):
    r, g, b = s2lin(np.asarray(c, float))
    return 0.2126*r + 0.7152*g + 0.0722*b

def contrast(c1, c2):
    a, b = rel_lum(c1), rel_lum(c2)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

# ------------------------------------------------------------- ink mixing
def multiply(*cs):
    out = np.ones(3)
    for c in cs: out = out * c
    return out

def screen(*cs):
    out = np.zeros(3)
    for c in cs: out = 1 - (1-out)*(1-c)
    return out

def tint(c, ground, k):
    """ink at partial coverage k over a ground (subtractive)."""
    return ground * (1 - k*(1 - c))

def candidates(inks, ground, night):
    """Everything this press can print, as (name, rgb)."""
    mix = screen if night else multiply
    out = []
    names = ["ink0", "ink1", "ink2"]
    for n, c in zip(names, inks): out.append((n, c))
    for i in range(3):
        for j in range(i+1, 3):
            out.append((f"{names[i]}x{names[j]}", mix(inks[i], inks[j])))
    out.append(("triple", mix(*inks)))
    for n, c in zip(names, inks):
        for k in (0.55, 0.30):
            out.append((f"{n}@{int(k*100)}", tint(c, ground, k) if not night
                                             else screen(ground, c*k)))
    return out

# ------------------------------------------------------------- retargeting
def in_gamut(lch, eps=1e-4):
    c = oklab2rgb(lch2lab(lch))
    return bool(np.all(c >= -eps) and np.all(c <= 1 + eps))

def max_chroma(L, H, hi=0.42, tries=32):
    """Largest chroma that still fits in sRGB at this lightness and hue."""
    lo = 0.0
    for _ in range(tries):
        mid = (lo + hi) / 2
        if in_gamut([L, mid, H]): lo = mid
        else: hi = mid
    return lo

# Every slot that could not be solved. The old behaviour was to return pure
# white or pure black and say nothing -- which discards the ink cast entirely,
# and is exactly the shape of silent failure that let this generator report
# "0 contrast failures" while shipping colours that missed their target. Nothing
# currently trips it; the point is that if something ever does, it will be loud.
FALLBACKS = []


def _fallback(ratio, hue, ground, night, where):
    c = np.ones(3) if night else np.zeros(3)
    FALLBACKS.append(dict(where=where, target=float(ratio), hue=round(float(hue), 1),
                          ground=rgb2hex(ground), result=rgb2hex(c)))
    print(f"warning: {where} could not reach {ratio}:1 at hue {hue:.0f} on "
          f"{rgb2hex(ground)}; fell back to {rgb2hex(c)} (ink cast lost)",
          file=sys.stderr)
    return c


def retarget(rgb, ground, min_ratio, night, tries=36):
    """Hit `min_ratio` against the ground while keeping as much of the ink's
    saturation as possible.

    Chroma and contrast are not independent: at a warm hue, adding chroma RAISES
    luminance, which lowers contrast on paper. Cutting chroma to recover the
    ratio drives the colour to grey. So we try saturations from full down, and
    for each one solve for the lightness that meets the ratio -- lightness does
    the work, chroma is preserved.
    """
    L0, C0, H = lab2lch(rgb2oklab(rgb))
    mc0 = max_chroma(L0, H)
    sat = min(C0 / mc0, 1.0) if mc0 > 1e-6 else 0.0
    Lg = lab2lch(rgb2oklab(ground))[0]

    def solve(k):
        lo, hi = (Lg, 0.995) if night else (0.02, Lg)
        best = None
        for _ in range(tries):
            L = (lo + hi) / 2
            c = np.clip(oklab2rgb(lch2lab([L, max_chroma(L, H)*sat*k, H])), 0, 1)
            if contrast(c, ground) >= min_ratio:
                best = c
                if night: hi = L
                else:     lo = L
            else:
                if night: lo = L
                else:     hi = L
        return best

    for k in (1.00, 0.94, 0.87, 0.79, 0.70, 0.60, 0.49, 0.37, 0.24, 0.12, 0.0):
        c = solve(k)
        if c is not None:
            return c
    return _fallback(min_ratio, H, ground, night, "retarget")


def neutral(ground, ratio, night):
    """A grey at an exact contrast ratio against the ground."""
    Lg = lab2lch(rgb2oklab(ground))[0]
    lo, hi = (Lg, 0.995) if night else (0.02, Lg)
    best = None
    for _ in range(40):
        L = (lo + hi) / 2
        c = np.clip(oklab2rgb(lch2lab([L, 0.0, 0.0])), 0, 1)
        if contrast(c, ground) >= ratio:
            best = c
            if night: hi = L
            else:     lo = L
        else:
            if night: lo = L
            else:     hi = L
    if best is not None:
        return best
    return _fallback(ratio, 0.0, ground, night, "neutral")

# ANSI slots and the OKLCh hue each one should sit nearest.
# Body-text contrast. Pushing this much past 13 on a dimmed ground makes the
# solver clip to pure #000000, which throws away the warm tint in the ink.
FG_CONTRAST = 13.0

SLOTS = [("red",25),("orange",55),("yellow",95),("green",145),
         ("cyan",195),("blue",255),("magenta",330),("brown",65)]

# Contrast target PER SLOT, deliberately not uniform.
#
# Driving every hue to the same ratio was the original design ("weight is
# uniform, so hue alone carries meaning"). Measured, it flattens lightness across
# the whole palette to 0.10-0.30 L* -- under the ~1.0 L* just-noticeable
# difference -- so hue becomes the ONLY thing separating two slots. That is
# exactly what colour-vision deficiency removes: simulated deuteranopia collapsed
# red against green to dE00 4.7-14.4, against 19.4 for naive terminal defaults.
# Spreading the targets restores a lightness difference that survives when hue
# perception does not. Red and green are the pair that carries pass/fail meaning,
# so they are pushed furthest apart.
# TUNED FOR THE NIGHT GROUND (themes.CANON_LEVEL). A deeper ground compresses
# perceived lightness, so it takes a higher ratio to buy the same separation --
# but it also leaves more headroom before a colour hits white. Re-check these
# against `bright_*` chroma if CANON_LEVEL ever changes: on the lifted `slate`
# ground these same numbers drive the bright variants to pure white.
SLOT_CONTRAST = {"red": 4.5, "orange": 5.4, "yellow": 9.2, "green": 10.0,
                 "cyan": 6.2, "blue": 5.0, "magenta": 5.8, "brown": 4.5}

# Light mode cannot use the numbers above, and not because they are unpleasant
# on paper -- because they are ABOVE THE CEILING. Contrast is solved against
# `selection`, the extreme of the three grounds that carry text. On the night
# ground that is #21242A and the most any colour can reach is 15.59:1. On the
# day ground it is #C3BFB8 and the ceiling is 11.51:1: paper reflects, so a
# light theme simply has less headroom. green at 10.0 + BRIGHT_DELTA + margin
# asks for 12.1:1, which no colour of any hue can deliver there, so retarget()
# gave up and shipped pure black with its ink cast gone.
#
# These are the dark targets compressed into the smaller headroom, NOT rescaled
# proportionally. A proportional scale would have taken red to 3.3 and broken
# WCAG AA for text, so the floor is pinned at 4.5 and only the top is squeezed:
# the [4.5, 10.0] range maps onto [4.5, 8.8], which keeps the ordering, keeps
# red and green furthest apart, and leaves green's bright variant at 10.9
# against a ceiling of 11.51.
# These are SEARCHED, not derived. Compressing the dark targets proportionally
# cleared the contrast ceiling but left three protanopia collisions, because
# under CVD hue separation is gone and lightness is the only channel left --
# which means the contrast targets ARE the separation. A search over the eight
# targets against the collision gate found this set: 0 contrast fallbacks, 0
# collisions, every pair clearing its floor.
#
# It is tight, and honestly so. green at 9.3 puts bright_green at 11.4 against a
# ceiling of 11.51 -- 0.11 to spare. BRIGHT_DELTA cannot absorb that: measured,
# every reduction buys ceiling headroom and costs collisions (1.8 -> 1 collision,
# 1.6 -> 2, 1.2 -> 5), because base and bright then sit too close to tell apart.
# Darkening the paper does not help either -- `selection` darkens with it, so the
# ceiling FALLS (0.080 -> 11.51, 0.140 -> 9.28).
#
# The day ground has just enough room and no more. If an ink or a ground moves,
# expect this to need re-searching; `--check day` is the feedback loop.
SLOT_CONTRAST_LIGHT = {"red": 4.5, "orange": 4.9, "yellow": 7.6, "green": 9.3,
                       "cyan": 6.7, "blue": 5.4, "magenta": 5.3, "brown": 4.5}


# Slate is a THIRD set, and finding out why reframed all of this: contrast
# targets are a function of the GROUND'S CEILING, not of light versus dark.
#
#   level   ground    selection   ceiling   max base target
#   night   #0D0F15   #21242A     15.59     13.5
#   slate   #212329   #373940     11.47      9.4
#   day     #DAD6CE   #C3BFB8     11.51      9.4
#
# Slate is a lifted dark ground, so the gap to white is squeezed exactly as
# paper squeezes the gap to black -- and its ceiling lands within 0.04 of day's.
# Feeding it the LIGHT targets took it from four collisions to none in one step;
# only green needed moving, from 9.3 to 9.0, because bright_green at 11.4 was
# above slate's 11.47 for a hue that cannot reach it with any chroma left.
#
# So these are keyed by level, not by mode. Night is the odd one out, and it is
# the odd one out because it is the only ground with real headroom.
SLOT_CONTRAST_SLATE = {"red": 4.5, "orange": 4.9, "yellow": 7.6, "green": 9.0,
                       "cyan": 6.7, "blue": 5.4, "magenta": 5.3, "brown": 5.1}

SLOT_CONTRAST_BY_LEVEL = {
    "night": SLOT_CONTRAST,
    "slate": SLOT_CONTRAST_SLATE,
    "day": SLOT_CONTRAST_LIGHT,
}


def slot_contrast(night, level=None):
    if level in SLOT_CONTRAST_BY_LEVEL:
        return SLOT_CONTRAST_BY_LEVEL[level]
    return SLOT_CONTRAST if night else SLOT_CONTRAST_LIGHT
# The bright_* variants sit this much above their base. It has to stay small:
# on a dark ground a high contrast target IS lightness, and pushing a hue that
# is already at 8:1 up another 2.9 drives it to literal white -- measured, five
# of eight bright slots lost all chroma and became the same colour. 2.0 keeps
# every bright variant recognisably its own hue.
BRIGHT_DELTA = 2.0
# retarget() solves to exactly the target, then rgb2hex quantises to 8 bits and
# the result lands a hair under it. Solve slightly high so the SHIPPED value
# clears the floor rather than the pre-quantisation one.
QUANT_MARGIN = 0.10

# ---------------------------------------------------------------- borders
# The active window border is the most-looked-at chrome on a tiling desktop, and
# shell.toml routes this same token into the lock screen, notifications, popups
# and menu cards -- so it is the one surface where the press either shows or
# doesn't. Three stops: an ink, what those two inks ACTUALLY make where they
# overlap on this ground, and the other ink. That middle stop is the whole point
# -- it is the only place in the theme where an overprint is visible as itself.
#
# Raw inks cannot be used. Measured against the night ground, #0F4C81 lands at
# 2.16 contrast (invisible as a border) and #FFE800 at 15.32 (glare), so every
# stop is retargeted to the accent's own weight -- the border then reads at the
# same volume as the rest of the theme instead of over it.
#
# The mix is tempered because the untempered screen-blend of blue and fluoro
# orange is #FF5388, a hot pink that dominates everything else on screen.
# Chroma comes off; lightness and hue are held, so it stays the colour the press
# would make, just quieter.
# Per mode, because the two blends start in completely different places.
# Measured, at the accent's own contrast:
#   dark  screen(blue, orange) -> #FF5388, 100% of max chroma at that lightness
#   light multiply(blue, orange) -> #2C445C,  48%
# On a dark ground the mix comes out a hot pink that dominates everything and
# has to be pulled back. On paper it arrives already subdued -- the inks absorb
# rather than glow -- so tempering it again only walks it toward grey (0.35
# takes 48% down to 31%). Light mode keeps its mix as the press made it.
BORDER_MIX_TEMPER = {"dark": 0.35, "light": 0.0}
# 45deg, not the 15deg primary screen angle. At border_size 2 a 15deg gradient
# collapses to flat colour on the side edges -- measured, not assumed -- because
# each edge traverses too little of the ramp. 45 keeps ink travelling on every
# edge at the width actually in use.
BORDER_ANGLE = 45

# ------------------------------------------------------- collision detection
# The generator has always failed a run when a colour could not reach its
# CONTRAST target. It never checked the other way a palette breaks: two slots
# solving to the same colour. That is the worse failure, because contrast
# fallbacks announce themselves as pure black or white while a collision just
# quietly makes two meanings look identical -- and this palette's whole claim is
# one-colour-one-meaning, verified under colour-vision deficiency.
#
# Vienot, Brettel & Mollon (1999): project LMS onto the plane a dichromat can
# still distinguish. Cheap, standard, and good enough to catch a collision.
_RGB2LMS = np.array([[17.8824,   43.5161,  4.11935],
                     [3.45565,   27.1554,  3.86714],
                     [0.0299566,  0.184309, 1.46709]])
_LMS2RGB = np.linalg.inv(_RGB2LMS)
_PLANE = {
    "deutan": np.array([[1, 0, 0], [0.494207, 0, 1.24827], [0, 0, 1]]),
    "protan": np.array([[0, 2.02344, -2.52581], [0, 1, 0], [0, 0, 1]]),
    "tritan": np.array([[1, 0, 0], [0, 1, 0], [-0.395913, 0.801109, 0]]),
}

# Slots that carry MEANING and must stay distinguishable from each other.
# Backgrounds are deliberately close and `accent` is `blue` by construction, so
# neither belongs here.
MEANING_SLOTS = ["red", "yellow", "orange", "green", "cyan", "blue", "magenta",
                 "brown"]
MEANING_SLOTS += ["bright_" + s for s in MEANING_SLOTS
                  if s not in ("orange", "brown")]

# REGRESSION FLOORS, not absolute perceptual thresholds. Each sits just under
# what the shipped night palette actually achieves, so this catches a change
# that makes separation worse rather than asserting a bar nothing meets:
#
#   shipped night palette   normal 0.0624   deutan 0.0185   protan 0.0392
#
# Re-measure these if CANON_LEVEL changes -- they are properties of that ground.
COLLISION_FLOOR = {"normal": 0.050, "deutan": 0.015, "protan": 0.030}
# Tritanopia is REPORTED, never enforced. The shipped palette's own tritan floor
# is 0.0029 (orange/bright_red), so a gate here would fail the thing it exists
# to protect. It is also ~0.01% of people against deuteranopia's ~6% of males,
# which is why the palette was tuned for the latter in the first place.
COLLISION_REPORT_ONLY = ("tritan",)

COLLISIONS = []


def simulate_cvd(rgb, kind):
    """rgb (0..1) as a dichromat of `kind` sees it."""
    lms = _RGB2LMS @ s2lin(np.asarray(rgb, float))
    return np.clip(lin2s(_LMS2RGB @ (_PLANE[kind] @ lms)), 0, 1)


def check_collisions(cols):
    """Record every meaning-slot pair that is too close to tell apart.

    Appends to COLLISIONS and returns it. Entries carry `enforced=False` for
    vision types that are reported rather than gated.
    """
    import itertools
    slots = [s for s in MEANING_SLOTS if s in cols]
    for kind in list(COLLISION_FLOOR) + list(COLLISION_REPORT_ONLY):
        lab = {}
        for s in slots:
            c = hex2rgb(cols[s]) if isinstance(cols[s], str) else np.asarray(cols[s])
            lab[s] = rgb2oklab(c if kind == "normal" else simulate_cvd(c, kind))
        floor = COLLISION_FLOOR.get(kind)
        worst = None
        for a, b in itertools.combinations(slots, 2):
            d = float(np.linalg.norm(lab[a] - lab[b]))
            if worst is None or d < worst[0]:
                worst = (d, a, b)
            if floor is not None and d < floor:
                COLLISIONS.append(dict(kind=kind, a=a, b=b, dist=d,
                                       floor=floor, enforced=True))
        if floor is None and worst is not None:
            COLLISIONS.append(dict(kind=kind, a=worst[1], b=worst[2],
                                   dist=worst[0], floor=None, enforced=False))
    return COLLISIONS


def build(name, inks_hex, paper, night_ground, night, ui_ground=None,
          fg_contrast=None, level=None):
    inks = [hex2rgb(h) for h in inks_hex]
    # The UI ground is deliberately dimmer than the wallpaper's paper, so the
    # terminal is comfortable to read and the bar does not vanish into the
    # wallpaper's paper margins.
    # ui_ground wins in BOTH modes -- the dark levels (slate, night) differ from
    # each other only by their ground, so ignoring it here collapses them.
    ground = hex2rgb(ui_ground or (night_ground if night else paper))
    paper_rgb, ink_rgb = hex2rgb(paper), hex2rgb(night_ground)
    fg_target = paper_rgb if night else ink_rgb

    # Three grounds carry text, not one. `selection` is the extreme of the set --
    # lightest in dark mode, darkest in light mode -- so a colour that clears its
    # target against `selection` clears it against `background` and
    # `lighter_background` too. Solving against `background` alone (which is what
    # this used to do) shipped 0/96 hue slots meeting target on the other two,
    # while the terminal puts syntax colours on `selection` for every visual
    # selection, and btop, gum and helix do the same.
    sel = neutral_shift(ground, +0.090 if night else -0.070)

    cands = candidates(inks, ground, night)
    # only genuinely coloured candidates may claim a colour slot -- a near-neutral
    # overprint will otherwise win a hue slot on distance alone and print grey.
    strong = [(n, c) for n, c in cands if lab2lch(rgb2oklab(c))[1] >= 0.045]
    if not strong: strong = cands
    mean_sat = float(np.mean([min(lab2lch(rgb2oklab(c))[1] /
                                  max(max_chroma(*lab2lch(rgb2oklab(c))[[0,2]]), 1e-6), 1.0)
                              for _, c in strong]))

    used, cols = set(), {}
    for slot, hue in SLOTS:
        scored = []
        for cname, c in strong:
            L, C, H = lab2lch(rgb2oklab(c))
            d = min(abs(H-hue), 360-abs(H-hue))
            scored.append((d + (75 if cname in used else 0), cname, c))
        scored.sort(key=lambda t: t[0])
        d, cname, c = scored[0]
        Ls, Cs, Hs = lab2lch(rgb2oklab(c))
        if d <= 12:
            # A real ink or overprint sits on this hue -- print it true.
            used.add(cname)
        else:
            # Nothing lands here. Synthesise AT THE SLOT HUE, inheriting this
            # press's lightness and saturation. Snapping to the nearest ink
            # instead lets two slots collapse onto one indistinguishable colour,
            # which destroys the one-colour-one-meaning contract.
            mc = max_chroma(Ls, Hs)
            sat_here = min(Cs / mc, 1.0) if mc > 1e-6 else mean_sat
            c = np.clip(oklab2rgb(lch2lab([Ls, max_chroma(Ls, hue)*sat_here, hue])), 0, 1)
            if d <= 30: used.add(cname)
        if slot == "brown":                      # brown is a dulled orange
            # ...but at ITS OWN hue. This used to hard-code 55.0, which is the
            # orange slot's hue exactly, while the collision penalty above was
            # scored against brown's declared hue of 65. The generator therefore
            # checked a palette it never emitted, and shipped orange and brown
            # three bytes apart (#A76C42 / #A66D45, dE_ok 0.0036 -- a fifth of a
            # JND). retarget() then renormalised chroma, discarding the x0.55
            # dulling that was supposed to separate them.
            L, C, H = lab2lch(rgb2oklab(c))
            c = np.clip(oklab2rgb(lch2lab([L, C*0.55, hue])), 0, 1)
        target = slot_contrast(night, level).get(slot, 4.5)
        cols[slot] = retarget(c, sel, target + QUANT_MARGIN, night)
        cols["bright_"+slot] = retarget(c, sel, target + BRIGHT_DELTA + QUANT_MARGIN,
                                        night)

    # Border stops, derived -- not chosen. Solved at the accent's own contrast so
    # the border never outshouts the palette, and mixed the way this ground
    # actually mixes: screen on a dark ground, multiply on paper.
    accent_rgb = cols["green" if name == "orchard" else "blue"]
    accent_hex = rgb2hex(accent_rgb)
    border_tgt = contrast(accent_rgb, ground)
    b_ink = retarget(inks[0], ground, border_tgt, night)
    o_ink = retarget(inks[1], ground, border_tgt, night)
    raw_mix = screen(inks[0], inks[1]) if night else multiply(inks[0], inks[1])
    b_mix = temper(retarget(raw_mix, ground, border_tgt, night),
                   BORDER_MIX_TEMPER["dark" if night else "light"])
    active_border = "%s %s %s %ddeg" % (
        rgba(b_ink), rgba(b_mix), rgba(o_ink), BORDER_ANGLE)
    # Unfocused windows recede into this theme's own ground rather than wearing
    # the stock generic grey, which is a colour Overprint never otherwise uses.
    inactive_border = rgba(neutral(ground, 1.55, night), "aa")

    return dict(
        mode="dark" if night else "light",
        # The three border stops, exposed by name so shell.toml can be built
        # from the same inks rather than re-deriving them. Not in KEY_ORDER, so
        # they never reach colors.toml.
        ink_primary=rgb2hex(b_ink),
        ink_mix=rgb2hex(b_mix),
        ink_secondary=rgb2hex(o_ink),
        background=rgb2hex(ground),
        dark_background=rgb2hex(neutral_shift(ground, -0.030 if night else -0.022)),
        darker_background=rgb2hex(neutral_shift(ground, -0.055 if night else -0.045)),
        lighter_background=rgb2hex(neutral_shift(ground, +0.045 if night else -0.008)),
        selection=rgb2hex(sel),
        foreground=rgb2hex(retarget(fg_target, ground, fg_contrast or FG_CONTRAST, night)),
        bright_foreground=rgb2hex(retarget(fg_target, ground, (fg_contrast or FG_CONTRAST) + 1.6, night)),
        light_foreground=rgb2hex(neutral(ground, 9.0, night)),
        dark_foreground=rgb2hex(neutral(ground, 5.2, night)),
        muted=rgb2hex(neutral(sel, 4.5 + QUANT_MARGIN, night)),
        accent=accent_hex,
        hyprland_active_border=active_border,
        hyprland_inactive_border=inactive_border,
        **{k: rgb2hex(v) for k, v in cols.items()})


def rgba(c, alpha="ee"):
    """Hyprland gradient stop. omarchy-theme-set-templates parses these into the
    Lua table form the compositor wants; the plain CSS-ish string is rejected."""
    return "rgba(%s%s)" % (rgb2hex(c).lstrip("#").lower(), alpha)


def temper(c, k):
    """Pull chroma toward neutral by k, holding lightness and hue."""
    L, C, H = lab2lch(rgb2oklab(c))
    return np.clip(oklab2rgb(lch2lab([L, C * (1 - k), H])), 0, 1)


def neutral_shift(ground, dL):
    L, C, H = lab2lch(rgb2oklab(ground))
    return np.clip(oklab2rgb(lch2lab([max(0.0, min(1.0, L + dL)), C, H])), 0, 1)
