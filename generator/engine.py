"""Risograph overprint engine, mk2.

Two changes over mk1, both from Seth's brief:

  ORDER    Compositions are derived from proportion systems, never placed by
           eye. Every edge lands on a module or a term of a series.

  CANOPY   Ink is never a single plate ramped light-to-dark. Several inks trade
           places locally while the total coverage holds steady -- so a field
           reads as one colour at arm's length and decomposes into distinct
           hues up close. The way a tree reads green.
"""
import math, cairo, numpy as np, zlib, struct

PHI = (1 + 5 ** 0.5) / 2
FIB = [1, 2, 3, 5, 8, 13, 21]

# Three inks now. Two opposed, one that lets the mix wander somewhere real.
ANGLES = [15.0, 75.0, 45.0]                 # classic separation angles
MISREG = [(0, 0), (3, -2), (-2, 2)]         # px -- the hand-made tell


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], float) / 255.0


# ------------------------------------------------------------------- masks
def mask(w, h, draw):
    surf = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)
    draw(ctx, w, h)
    surf.flush()
    buf = np.frombuffer(surf.get_data(), np.uint8).reshape(h, surf.get_stride())[:, :w]
    return buf.astype(np.float32) / 255.0


# ------------------------------------------------------------------- noise
def lowpass_noise(h, w, scale, rng):
    """Isotropic smooth noise, unit variance. `scale` ~ feature size in px."""
    n = rng.normal(0, 1, (h, w))
    F = np.fft.rfft2(n)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    F *= np.exp(-((np.sqrt(fy ** 2 + fx ** 2) * scale) ** 2))
    out = np.fft.irfft2(F, s=(h, w)).astype(np.float32)
    s = out.std()
    return (out - out.mean()) / s if s > 1e-9 else out


def canopy(cov_list, rng, amp=0.22, scales=(20, 30, 44)):
    # Scales must stay above the halftone lattice's Nyquist limit (2*cell).
    # Below it the canopy's ink-trading is finer than the screen can
    # resolve, so it is sampled away instead of showing as local hue drift --
    # measured, 97.5% of a field's energy sat at the lattice frequency and
    # only 2.5% in the canopy band.
    """Let the inks trade places locally without changing total coverage.

    This is the whole leaf idea: sum(cov) is preserved pixel by pixel, but WHICH
    ink supplies it wanders across the field.
    """
    covs = [c.copy() for c in cov_list]
    total = sum(covs)
    h, w = total.shape
    noises = [lowpass_noise(h, w, scales[i % len(scales)], rng) for i in range(len(covs))]
    # zero-sum the noise set so redistribution is conservative
    mean_n = sum(noises) / len(noises)
    noises = [n - mean_n for n in noises]
    # exp keeps every plate strictly positive -- a linear (1 + amp*n) term can
    # go negative on a strong noise excursion and punch white holes in solid ink.
    covs = [c * np.exp(amp * n) for c, n in zip(covs, noises)]
    s = sum(covs)
    scale = np.divide(total, s, out=np.zeros_like(s), where=s > 1e-6)
    return [c * scale for c in covs]


def halftone(cov, angle_deg, cell):
    h, w = cov.shape
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    a = math.radians(angle_deg)
    u = (x * math.cos(a) + y * math.sin(a)) / cell
    v = (-x * math.sin(a) + y * math.cos(a)) / cell
    du, dv = u - np.round(u), v - np.round(v)
    d = np.sqrt(du * du + dv * dv) / 0.7071
    # Printed area is pi*(r*0.7071*cell)^2 = (pi/2)*cov*cell^2, so a naive
    # r = sqrt(cov) lays down pi/2 (1.571x) too much ink: the screen saturates at
    # cov 0.637 and everything above that prints as flat solid instead of a dot
    # pattern. sqrt(2/pi) rescales the radius so printed area tracks coverage.
    r = np.sqrt(np.clip(cov, 0, 1)) * 0.79788
    edge = np.clip((r - d) * cell * 0.9 + 0.5, 0, 1)
    # The +0.5 above is the antialiasing midpoint: d == r should give half a
    # pixel of ink. But at ZERO coverage r is 0 and the cell centre has d 0, so
    # it returned 0.5 there too -- half ink at the centre of every cell of blank
    # ground. That sprayed ~200 bright specks through the top 30px strip alone,
    # and at gaps_out=10 that margin is the only part of a wallpaper on screen,
    # so the stray specks were the only wallpaper pixels visible while working.
    # Fade the dot out once its radius drops below about a pixel.
    return edge * np.clip(r * cell * 1.8, 0, 1)


# Everything in compose.py is fractional, so compositions are already
# resolution-independent. These three are not: the halftone pitch, the
# misregistration offset and the canopy band are all in PIXELS, tuned at
# REFERENCE_WIDTH. Render wider without scaling them and the screen gets
# relatively finer, the misregistration relatively tighter and the canopy
# relatively smaller -- a different-looking print, not a bigger one.
REFERENCE_WIDTH = 2560


def render(w, h, plates, palette, night=False, cell=9.0, grain=0.018,
           amp=0.22, seed=0, scale=None):
    """plates: list of coverage arrays, one per ink (values 0..1).

    scale defaults to w / REFERENCE_WIDTH, which keeps a render at any size
    looking like the same press rather than the same press photographed closer.
    """
    if scale is None:
        scale = w / REFERENCE_WIDTH
    cell = cell * scale
    canopy_scales = tuple(max(2.0, v * scale) for v in (20, 30, 44))
    rng = np.random.default_rng(seed)
    plates = canopy(plates, rng, amp=amp, scales=canopy_scales)
    ground = hex2rgb(palette["night"] if night else palette["paper"])
    out = np.ones((h, w, 3), np.float32) * ground

    for i, cov in enumerate(plates):
        ink = hex2rgb(palette["inks"][i])
        dots = halftone(cov, ANGLES[i % 3], cell)
        dx, dy = MISREG[i % 3]
        dx, dy = int(round(dx * scale)), int(round(dy * scale))
        dots = np.roll(np.roll(dots, dy, 0), dx, 1)[..., None]
        if night:
            out = 1.0 - (1.0 - out) * (1.0 - dots * ink)   # inks glow
        else:
            out = out * (1.0 - dots * (1.0 - ink))         # inks absorb

    out = np.clip(out + rng.normal(0, grain, (h, w, 1)).astype(np.float32), 0, 1)
    return (out * 255).astype(np.uint8)


def write_png(path, rgb):
    h, w, _ = rgb.shape
    raw = b"".join(b"\x00" + rgb[y].tobytes() for y in range(h))
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c))
    open(path, "wb").write(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b""))
