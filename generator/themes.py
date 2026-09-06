"""The four presses. Two opposed inks plus a warm third that lets the mix travel."""
INKS = {
    "harbour": ["#0F4C81", "#FF5A4D", "#FFE800"],   # blue   / fluoro orange / yellow
    "orchard": ["#00A95C", "#FF48B0", "#FFE800"],   # green  / fluoro pink   / yellow
    "ember":   ["#765BA7", "#F65058", "#FFE800"],   # purple / scarlet       / yellow
    "tidal":   ["#00838A", "#F65058", "#FFAE00"],   # teal   / scarlet       / gold
}
GROUNDS = {
    "harbour": ("#F4F0E8", "#14161C"),
    "orchard": ("#F2F1EA", "#111614"),
    "ember":   ("#F5F2EA", "#16131C"),
    "tidal":   ("#F1F1EC", "#101618"),
}

# Day mode was too bright to work in: paper at OKLab L~0.956 is near paper-white
# on a bright panel. Both grounds are pulled down, the UI further than the
# wallpaper, so windows and the bar also read as distinct FROM the wallpaper
# instead of dissolving into its paper margins.
#
# Raise these to dim further; set both to 0.0 for the original paper-white.
DAY_WALLPAPER_DIM = 0.045   # OKLab L subtracted from the wallpaper's paper
DAY_UI_DIM        = 0.080   # ... and from the UI ground (bar, terminal, menus)

# Three levels, not two. One dark palette cannot serve both a sunlit room and a
# dark one: in glare a very deep ground washes out and low-contrast text becomes
# unreadable, while at night that same crispness is harsh. So dark splits into
# SLATE (lifted ground, full contrast, survives daylight) and NIGHT (deeper
# ground, gentler contrast, for a dark room).
SLATE_LIFT      = 0.055     # OKLab L added to the base dark ground
SLATE_WALL_LIFT = 0.035
NIGHT_DEEPEN    = 0.030     # ... and subtracted, for the deep variant

# Body-text contrast per level. Night is deliberately lower: maximum contrast in
# a dark room is what makes long sessions hurt.
# Day is NOT 13.0. bright_foreground is fg_contrast + 1.6, and against the day
# ground (#DAD6CE) the absolute ceiling is 14.49:1 -- so 13.0 asked for 14.6:1,
# above what pure black achieves, and it fell back to #000000. 11.0 puts the
# bright variant at 12.6 with real headroom, and 11:1 on paper is still far past
# WCAG AAA (7:1) for body text.
LEVEL_FG = {"day": 11.0, "slate": 13.0, "night": 10.0}
LEVELS   = ("day", "slate", "night")

def _shift(hex_color, amount):
    import palette as P, numpy as np
    L, C, H = P.lab2lch(P.rgb2oklab(P.hex2rgb(hex_color)))
    return P.rgb2hex(np.clip(P.oklab2rgb(P.lch2lab([min(1.0, max(0.0, L + amount)), C, H])), 0, 1))

def is_dark(level):
    return level != "day"

def level_ground(press, level):
    paper, dark = GROUNDS[press]
    if level == "day":   return _shift(paper, -DAY_UI_DIM)
    if level == "slate": return _shift(dark, +SLATE_LIFT)
    return _shift(dark, -NIGHT_DEEPEN)

def level_wallpaper(press, level):
    """The ground the WALLPAPER prints on -- always a touch lighter than the UI,
    so windows and the bar read as distinct objects sitting on it."""
    paper, dark = GROUNDS[press]
    if level == "day":   return _shift(paper, -DAY_WALLPAPER_DIM)
    if level == "slate": return _shift(dark, +SLATE_WALL_LIFT)
    return _shift(dark, -NIGHT_DEEPEN)



# The single Overprint theme takes one press's inks and one level's ground. The
# other presses and levels survive as wallpapers, which is where the red-team
# found their differences actually were: measured, the four presses' accents sat
# 0.020 apart in OKLab and their day grounds 0.007 -- roughly three times below a
# just-noticeable difference -- so they were never four palettes in practice.
CANON_PRESS = "harbour"
CANON_LEVEL = "night"
