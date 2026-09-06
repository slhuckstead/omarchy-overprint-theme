"""Compositions for Overprint.

Every layout is derived from one ratio. A diminishing nested series, few large
fields, one dominant, no visible grid -- rungs 3 and 4 of the structure ladder.
Nothing here is placed by eye; if you cannot write it as a rule, it does not go in.
"""
import math, numpy as np, engine
from engine import PHI

def _build(w, h, elements, ninks=3):
    plates = [np.zeros((h, w), np.float32) for _ in range(ninks)]
    for draw, mix in elements:
        m = engine.mask(w, h, draw)
        # Lay each field down as ink ON TOP of what is there, not added to it.
        # Summing made nested elements accumulate past any real press: modulor
        # nests four deep, so its inner fields clipped to 1.3 on all three plates
        # and printed as a black blot on paper and a white glare slab on a dark
        # ground -- in the very variant used as every theme's preview image.
        for i, k in enumerate(mix):
            plates[i] = plates[i] * (1.0 - m) + m * k
    return plates

def _rect(x, y, ww, hh, a=1.0):
    def d(c, w, h):
        c.set_source_rgba(0, 0, 0, a); c.rectangle(x*w, y*h, ww*w, hh*h); c.fill()
    return d

# Mixes are ink recipes, not colours: how much of each plate lands in a field.
MIXES = [(.95,0,0), (0,.90,0), (0,0,.92), (.85,.30,0), (0,.55,.75),
         (.60,0,.55), (.30,.85,0), (0,.75,.35)]

def canon(w, h, depth=5, vert=True, rot=0, margin=1/16):
    """Recursive golden-section subdivision. One rule makes the whole image."""
    e, a = [], 1/PHI
    def split(x, y, ww, hh, d, v):
        mix = MIXES[(d + rot) % len(MIXES)]
        if d == 0:
            e.append((_rect(x, y, ww, hh), mix)); return
        if v:
            e.append((_rect(x, y, ww*a, hh), mix))
            split(x+ww*a, y, ww*(1-a), hh, d-1, not v)
        else:
            e.append((_rect(x, y, ww, hh*a), mix))
            split(x, y+hh*a, ww, hh*(1-a), d-1, not v)
    split(margin, margin, 1-2*margin, 1-2*margin, depth, vert)
    return _build(w, h, e)

def modulor(w, h, layers=5, rot=0, bias=0.62, margin=1/12):
    """Nested proportional rectangles, each inset by 1-1/phi, with the classic
    asymmetric margin -- Albers' Homage logic."""
    e = []; x = y = margin; ww = hh = 1 - 2*margin
    hh = min(hh, 1 - 2*margin)
    for k in range(layers):
        e.append((_rect(x, y, ww, hh), MIXES[(k + rot) % len(MIXES)]))
        iw, ih = ww*(1-1/PHI), hh*(1-1/PHI)
        x, y = x + iw*bias, y + ih*(1-bias)
        ww, hh = ww - iw, hh - ih
    return _build(w, h, e)

def duo(w, h, rot=0, margin=1/16):
    """The calmest possible member of the family: a single phi split."""
    a = 1/PHI; m = margin
    e = [(_rect(m, m, (1-2*m)*a, 1-2*m), MIXES[rot % len(MIXES)]),
         (_rect(m + (1-2*m)*a, m, (1-2*m)*(1-a), (1-2*m)*a), MIXES[(rot+2) % len(MIXES)]),
         (_rect(m + (1-2*m)*a, m + (1-2*m)*a, (1-2*m)*(1-a), (1-2*m)*(1-a)),
          MIXES[(rot+4) % len(MIXES)])]
    return _build(w, h, e)


def spiral(w, h, turns=8, rot=0, margin=1/16):
    """The Fibonacci square tiling -- the golden spiral's own construction.

    Squares are taken off the short end of a golden rectangle, cycling
    left/top/right/bottom, each leaving another golden rectangle behind. The
    panel is 2560x1600, an aspect of 1.6 against phi's 1.618, so the remainder
    stays a golden rectangle all the way down.

    Worked in units of the HEIGHT (u spans 0..aspect, v spans 0..1) so a square
    is square on screen; fractional coordinates would shear it by the aspect.
    """
    from engine import FIB                      # G5: defined, never used -- now it is
    ar = w / float(h)
    e = []
    m = margin
    u, v, uw, vh = m * ar, m, (1 - 2*m) * ar, 1 - 2*m
    for k in range(turns):
        if uw <= 1e-6 or vh <= 1e-6:
            break
        side = min(uw, vh)
        phase = k % 4
        if uw >= vh:
            ux = u if phase == 0 else u + uw - side
            e.append((_rect(ux / ar, v, side / ar, vh), MIXES[(k + rot) % len(MIXES)]))
            if phase == 0:
                u += side
            uw -= side
        else:
            vy = v if phase == 1 else v + vh - side
            e.append((_rect(u / ar, vy, uw / ar, side), MIXES[(k + rot) % len(MIXES)]))
            if phase == 1:
                v += side
            vh -= side
    if uw > 1e-6 and vh > 1e-6:                 # the eye of the spiral
        e.append((_rect(u / ar, v, uw / ar, vh), MIXES[(turns + rot) % len(MIXES)]))
    return _build(w, h, e)


def stack(w, h, bands=6, rot=0, margin=1/16):
    """Horizontal bands at Fibonacci heights. The calmest composition in the
    set: no nesting, no focal point, just a spot-colour run down the sheet."""
    from engine import FIB
    f = FIB[:bands]
    total = float(sum(f))
    e, y, H = [], margin, 1 - 2*margin
    for k, fk in enumerate(f):
        hh = H * fk / total
        e.append((_rect(margin, y, 1 - 2*margin, hh), MIXES[(k + rot) % len(MIXES)]))
        y += hh
    return _build(w, h, e)


def register(w, h, rot=0, margin=1/7, spread=0.055):
    """A misregistration study: one golden block, printed twice, off by a hair.

    TWO plates, not three. Three inks fully overlapped screen-blend to near-white
    on a dark ground -- the centre washed out and the fringes, which are the
    whole point, barely read. With two, the overlap is a genuine two-ink
    overprint and the offset leaves a band of each ink alone down opposite
    edges: the classic tell of a plate that did not line up.

    Built plate-by-plate rather than through _build, which lays fields down
    opaquely and would have the second plate erase the first.
    """
    plates = [np.zeros((h, w), np.float32) for _ in range(3)]
    ar = w / float(h)
    bw = 1 - 2*margin
    bh = min(bw / PHI * ar * 0.62, 1 - 2*margin)
    y0 = (1 - bh) / 2
    pair = [(rot % 3), ((rot + 1) % 3)]
    offs = [(-spread / 2, -spread / 2 * 0.5), (spread / 2, spread / 2 * 0.5)]
    for j, (dx, dy) in zip(pair, offs):
        m = engine.mask(w, h, _rect(margin + dx, y0 + dy, bw, bh))
        plates[j] = np.maximum(plates[j], m * 0.92)
    return plates


# name, callable, kwargs, flip(x, y)
VARIANTS = [
    ("1-canon-recto",   canon,   dict(depth=5, vert=True,  rot=0), (False, False)),
    ("2-canon-verso",   canon,   dict(depth=5, vert=False, rot=2), (True,  False)),
    ("3-canon-deep",    canon,   dict(depth=6, vert=True,  rot=4), (False, True)),
    ("4-modulor",       modulor, dict(layers=5, rot=1, bias=0.62), (False, False)),
    ("5-modulor-wide",  modulor, dict(layers=4, rot=3, bias=0.34), (True,  False)),
    ("6-duo",           duo,     dict(rot=5),                      (False, False)),
    ("7-spiral",        spiral,  dict(turns=8, rot=0),             (False, False)),
    ("8-spiral-verso",  spiral,  dict(turns=7, rot=3),             (True,  True)),
    ("9-stack",         stack,   dict(bands=6, rot=2),             (False, False)),
    ("10-register",     register, dict(rot=0),                      (False, False)),
    ("11-register-alt", register, dict(rot=2, spread=0.035),        (True,  False)),
]

def make(name, w, h):
    for n, fn, kw, (fx, fy) in VARIANTS:
        if n != name: continue
        plates = fn(w, h, **kw)
        if fx: plates = [np.ascontiguousarray(p[:, ::-1]) for p in plates]
        if fy: plates = [np.ascontiguousarray(p[::-1, :]) for p in plates]
        return plates
    raise KeyError(name)
