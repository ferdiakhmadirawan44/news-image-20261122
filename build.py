#!/usr/bin/env python3
"""build.py — render the make.fun news-image-20261122 entry.

A single 1024x1024 newspaper front page summing up Sunday 22 November
2026, drawn entirely in code with Pillow. No photos, no downloaded
images, no network, no timestamps, no randomness: two runs write
byte-identical PNGs.

Design (broadsheet rules):
  * sharp rectangles divided by 1px hairline rules, 0px corner radius,
    no rounded cards; a 3px double rule under the masthead;
  * one dominant lead — COP31 spans the widest columns (4 of 6) with
    the largest headline; the other two heroes are secondary, stacked
    in the remaining 2 columns;
  * one spot colour: black ink on warm off-white paper (#F1ECE0);
    red is used only for small kickers, the dateline, tags and the
    pull-quote. Region-bar colours are kept. Illustrations are
    black + red + at most one muted accent (amber), flat shapes;
  * white space is left where a zone runs short — body type never
    goes below 10px to fill a gap;
  * two families only: DejaVu Serif Bold for headlines, DejaVu Sans
    for body and labels; body left-aligned; labels in spaced caps;
  * one consistent 6-column grid for the whole page, 1px vertical
    rules between columns.

Run: python3 build.py   -> writes entry.png next to this file.
"""

import hashlib

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 17                      # side margin; content width 990
CW = W - 2 * M              # 990
COL = 155                   # 6 columns: 6*155 + 5*12 = 990
GUT = 12

PAPER = (241, 236, 224)     # #F1ECE0 warm off-white
INK = (17, 17, 17)          # #111111
RED = (166, 27, 27)         # #A61B1B the one spot colour
AMBER = (166, 124, 26)      # muted gold, the single illustration accent
GREY = (120, 116, 108)
DARK = (14, 14, 18)         # near-black for night illustrations
CHAR = (38, 38, 44)         # charcoal buildings
MIDGREY = (138, 138, 138)
LIGHT = (221, 221, 221)
SHEET = (250, 247, 239)     # the COP31 text sheet
TAN = (216, 205, 180)       # map continents (the map's muted accent)
PANEL = (228, 220, 198)     # light panel behind mini icons

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def wrap(d, text, fnt, max_w):
    """Greedy word wrap; returns a list of lines, each <= max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if d.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def spaced(d, x, y, text, fnt, fill, track=1):
    """Draw text in spaced caps, one glyph at a time. Returns width."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=fnt, fill=fill)
        cx += d.textlength(ch, font=fnt) + track
    return cx - x - track


def spaced_w(d, text, fnt, track=1):
    w = 0
    for ch in text:
        w += d.textlength(ch, font=fnt) + track
    return w - track


def centre(d, cx, y, text, fnt, fill):
    d.text((cx - d.textlength(text, font=fnt) / 2, y), text,
           font=fnt, fill=fill)


def dot(d, cx, cy, r, fill):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def starburst(d, cx, cy, r_out, r_in, n, fill):
    import math
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.pi * i / n - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=fill)


def tag(d, x, y, text, kind):
    """Certainty tag: a sharp-cornered box (no radius), RIGHT-aligned
    so x is the box's right edge.
    CONFIRMED = solid black box, white text. REPORTED = paper box,
    1px red outline, red text."""
    fnt = font(SANS_B, 9)
    w = int(d.textlength(text, font=fnt)) + 10
    h = 14
    x = x - w
    if kind == "CONFIRMED":
        d.rectangle([x, y, x + w, y + h], fill=INK)
        d.text((x + 5, y + 2), text, font=fnt, fill=PAPER)
    else:
        d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=RED, width=1)
        d.text((x + 5, y + 2), text, font=fnt, fill=RED)
    return w


def tag_w(d, text):
    return int(d.textlength(text, font=font(SANS_B, 9))) + 10


# ------------------------------------------------------------- the news
# Every number below was verified against 2+ sources on 23 Nov 2026.
# Where sources conflicted (HK turnout, Dymer casualties) the number is
# left out rather than guessed.

HERO_LEAD = {
    "num": "1",
    "kicker": "ANTALYA, TÜRKIYE — CLIMATE",
    "headline": "COP31 collapses — no deal",
    "body": ("The final text dropped every mention of fossil fuels. The EU, UK, "
             "Panama, Marshall Islands and Norway refused to endorse it. "
             "President Murat Kurum: “no agreement on this text.” First no-deal "
             "COP since 2000 (COP6, The Hague); the longest ever, 44 hours "
             "overtime, two days late. The text kept 35% clean electricity by "
             "2035, dropped the $120bn adaptation target and admitted the "
             "1.5°C overshoot."),
    "quote": "“No agreement on this text.” — COP31 President Murat Kurum",
    "source": "Reuters · Politico · The Times · BBC",
    "tag": "CONFIRMED",
}

HERO_2 = {
    "num": "2",
    "kicker": "UKRAINE, OVERNIGHT — WAR",
    "headline": "Russia fires 186 drones; 161 downed",
    "body": ("Russia fired 186 drones overnight; Ukraine downed or suppressed "
             "161, including 56 jet-powered. A block in Dymer was partly "
             "destroyed: 14 missing, at least two killed."),
    "source": "Ukrainian Air Force · Reuters",
    "tag": "CONFIRMED",
}

HERO_3 = {
    "num": "3",
    "kicker": "BENGHAZI, LIBYA — WAR",
    "headline": "Sea drones strike Russian warship",
    "body": ("Suspected Ukrainian sea drones hit the Russian corvette Merkury "
             "at Benghazi: six drones, four intercepted, two struck. Serious "
             "damage and fire."),
    "source": "Libyan military officials · Reuters",
    "tag": "REPORTED",
}

MINIS = [
    ("4", "HONG KONG — ELECTIONS", "Hong Kong elects its Election Committee",
     "856 candidates for 723 seats in the city’s biggest polls since the overhaul. (SCMP)",
     "CONFIRMED", "ballot"),
    ("5", "LAS VEGAS — FORMULA 1", "Verstappen wins the Las Vegas GP",
     "75th win, 0.639s clear of Norris; Russell hits the wall late, finishes fifth. (F1)",
     "CONFIRMED", "race"),
    ("6", "WELLINGTON — CRICKET", "India declare on a record 720/9",
     "Record Test total in New Zealand; the hosts close on 119/2. (Cricbuzz · Reuters)",
     "CONFIRMED", "cricket"),
    ("7", "KHARTOUM — WAR", "Drones strike homes near Khartoum",
     "Strikes hit homes and a UN building; four killed, counts vary. (AFP)",
     "REPORTED", "drone"),
    ("8", "GAZA CITY — CONFLICT", "Israeli fire kills four in Gaza",
     "Three killed in a food vehicle; Hamas seeks urgent talks after an aid strike. (Al Jazeera)",
     "REPORTED", "flame"),
    ("9", "TEHRAN — ENERGY", "Iran begins rolling power cuts",
     "Up to two hours a day as gas output falls; rationing starts. (Reuters · AFP)",
     "CONFIRMED", "power"),
    ("10", "SERANG, INDONESIA — DISASTER", "Candy-factory fire kills three",
     "Blaze tore through the Banten plant; 36 missing, search goes on. (Detiknews)",
     "REPORTED", "factory"),
    ("11", "GULF OF FINLAND — SEA", "Russian cargo ship Sparta II still burning",
     "Ablaze after a drone strike; towed out of Finnish waters. (Reuters)",
     "REPORTED", "ship"),
    ("12", "BRASÍLIA — HEALTH", "Bolsonaro in intensive care",
     "Bowel obstruction, stable, breathing on his own. (Reuters · Al Jazeera)",
     "CONFIRMED", "cross"),
    ("13", "VATICAN CITY — FAITH", "Pope Leo XIV hosts 1,300 poor guests",
     "Lunch for the 10th World Day of the Poor. (Vatican News)",
     "CONFIRMED", "dome"),
    ("14", "KORDOFAN, SUDAN — WAR", "Sudan army retakes 30 towns in Kordofan",
     "Army says the push retook 30 towns in the west. (BBC)",
     "REPORTED", "map"),
    ("15", "NICOSIA — DIPLOMACY", "Cyprus expels two Russian diplomats",
     "Over suspected espionage. (euronews)",
     "CONFIRMED", "passport"),
]

ALSO = [
    ("16", "BepiColombo enters Mercury orbit", "after an eight-year journey. (ESA)"),
    ("17", "Nvidia faces an SEC probe", "accounting inquiry at an early stage as AI shares slide. (Straits Times · CNBC)"),
    ("18", "Seoul: education minister’s resignation accepted", "after the college-exam row. (Reuters)"),
    ("19", "Snow strands about 1,500 in a Japan village", "heavy snow blocks the roads in Fukushima. (dpa)"),
    ("20", "Wembanyama scores 50 as Spurs beat Pelicans", "50 points, 19 rebounds; San Antonio 114–91. (AP)"),
    ("21", "Kenya discharges its last Ebola patient", "outbreak declared over. (Wires)"),
    ("22", "Nepal PM Balendra Shah begins India visit", "his first foreign trip, 22–23 Nov. (IANS)"),
    ("23", "Denmark expels a Russian attaché", "over an alleged spy plot. (Guardian)"),
    ("24", "World Court: Myanmar committed genocide", "against the Rohingya, judges rule. (Guardian)"),
    ("25", "England beat New Zealand 27-12 in rugby", "at Twickenham. (Reuters)"),
    ("26", "Zverev v Alcaraz in the ATP Finals", "final in Turin."),
    ("27", "Estonia to shut its Russia border from 1 Dec", "after a sabotage bid. (Reuters)"),
    ("28", "Melbourne: 70 years since the 1956 Olympics opened", "The 1956 Games opened on this day 70 years ago. (ABC)"),
    ("29", "Hamas seeks urgent talks after an aid strike", "three in a food vehicle in Gaza City. (Al Jazeera · Anadolu)"),
    ("30", "Saudi-led coalition intercepts a Houthi drone", "and a ballistic missile aimed west and south."),
]

NUMBERS = [
    ("186", "DRONES FIRED"),
    ("161", "DOWNED"),
    ("0", "DEALS AT COP31"),
    ("6", "SEA DRONES"),
    ("856", "HK CANDIDATES"),
    ("720/9", "INDIA’S TEST TOTAL"),
]

REGIONS = [
    ("EUROPE", 8, (0, 110, 110)),
    ("MIDDLE EAST", 4, (166, 27, 27)),
    ("AMERICAS", 4, (40, 90, 160)),
    ("ASIA-PACIFIC", 5, (200, 120, 30)),
    ("AFRICA", 4, (40, 130, 70)),
    ("OCEANIA", 2, (110, 90, 160)),
    ("WORLD", 3, (110, 110, 110)),
]

DATE_CHECK = ("Every story on this page happened or was first reported on "
              "Sunday 22 November 2026 (UTC). Left out because they happened "
              "on an earlier day: Peru quake (Fri 20 Nov) · “El Chapo Isidro” "
              "captured (Fri 20 Nov) · Bayelsa boat, 24 dead (Fri 20 Nov) · "
              "400-drone night and Kryvyi Rih strike (Fri 20–Sat 21 Nov) · "
              "Gaza aid-van strike (Sat 21 Nov).")

SOURCES = ("Sources: Reuters · BBC · AP · AFP · Al Jazeera · The Guardian · "
           "SCMP · F1 · Cricbuzz · Detiknews · Vatican News · ESA · dpa. "
           "Scenes are drawn illustrations, not photographs. "
           "Wires read to 23:45 UTC, 22 Nov 2026.")

# ------------------------------------------------------- hero art (flat,
# black + red + at most one muted amber accent)

def art_cop31(d, x0, y0, x1, y1):
    """The words that killed the deal: a white text sheet on black,
    FOSSIL FUELS struck through in red, a NO DEAL stamp."""
    d.rectangle([x0, y0, x1, y1], fill=INK)
    sx0, sy0, sx1, sy1 = x0 + 130, y0 + 14, x1 - 130, y1 - 52
    d.rectangle([sx0, sy0, sx1, sy1], fill=SHEET)
    fnt = font(SANS_B, 20)
    centre(d, (sx0 + sx1) // 2, sy0 + 10, "FOSSIL", fnt, INK)
    centre(d, (sx0 + sx1) // 2, sy0 + 36, "FUELS", fnt, INK)
    d.line([(sx0 + 16, sy0 + 24), (sx1 - 16, sy0 + 56)], fill=RED, width=6)
    sx, sy = x1 - 168, y1 - 44
    d.rectangle([sx, sy, sx + 152, sy + 36], outline=RED, width=4)
    d.text((sx + 76, sy + 17), "NO DEAL", font=font(SANS_B, 21),
           fill=RED, anchor="mm")


def art_ukraine(d, x0, y0, x1, y1):
    """Night skyline under attack: charcoal towers, amber windows,
    grey drones, one red burst on the damaged tower."""
    d.rectangle([x0, y0, x1, y1], fill=DARK)
    towers = [(0, 34, 52), (36, 26, 78), (76, 18, 64), (112, 30, 88),
              (150, 22, 70), (188, 28, 80), (226, 20, 66), (262, 26, 74)]
    for tx, th, tw in towers:
        bx0, by1 = x0 + tx, y1
        d.rectangle([bx0, by1 - th, bx0 + 26, by1], fill=CHAR)
        for wy in range(by1 - th + 5, by1 - 4, 8):
            for wx in (bx0 + 5, bx0 + 14):
                d.rectangle([wx, wy, wx + 4, wy + 4], fill=AMBER)
    # drones: small grey crosses with red lights
    for dx, dy in [(52, 14), (120, 8), (196, 12), (262, 8), (300, 16)]:
        cx, cy = x0 + dx, y0 + dy
        d.line([(cx - 6, cy), (cx + 6, cy)], fill=LIGHT, width=2)
        d.line([(cx, cy - 4), (cx, cy + 4)], fill=LIGHT, width=2)
        dot(d, cx + 7, cy, 2, RED)
    # bursts: amber, except the damaged tower (red)
    starburst(d, x0 + 96, y0 + 16, 9, 4, 8, AMBER)
    starburst(d, x0 + 238, y0 + 20, 8, 3, 8, AMBER)
    starburst(d, x0 + 152, y0 + 12, 11, 4, 8, RED)


def art_benghazi(d, x0, y0, x1, y1):
    """A grey warship on a black sea, red fire where the drones hit."""
    d.rectangle([x0, y0, x1, y1], fill=DARK)
    d.ellipse([x1 - 34, y0 + 6, x1 - 12, y0 + 28], fill=PAPER)
    for yy in range(y0 + 34, y1 - 4, 7):
        d.line([(x0 + 8, yy), (x1 - 8, yy)], fill=(58, 58, 64), width=1)
    # sea drones: low dark hulls with red lights, wakes behind
    for dx in (36, 78):
        cx, cy = x0 + dx, y0 + 40
        d.line([(cx - 26, cy + 4), (cx, cy)], fill=LIGHT, width=1)
        d.rectangle([cx, cy - 3, cx + 16, cy + 3], fill=(60, 60, 66))
        dot(d, cx + 4, cy - 5, 2, RED)
    # the corvette Merkury
    d.rectangle([x0 + 118, y0 + 22, x0 + 292, y0 + 40], fill=MIDGREY)
    d.rectangle([x0 + 118, y0 + 40, x0 + 292, y0 + 46], fill=(100, 100, 100))
    d.rectangle([x0 + 200, y0 + 8, x0 + 208, y0 + 22], fill=MIDGREY)
    for wx in range(x0 + 132, x0 + 284, 22):
        d.rectangle([wx, y0 + 27, wx + 10, y0 + 35], fill=AMBER)
    starburst(d, x0 + 292, y0 + 26, 13, 5, 8, RED)


# ------------------------------------------------------- mini icons
# (flat, black + red + at most one muted amber accent)

def icon_ballot(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PANEL)
    d.rectangle([x0 + 30, y0 + 9, x0 + 62, y0 + 20], fill=SHEET,
                outline=INK, width=1)
    d.line([(x0 + 36, y0 + 9), (x0 + 56, y0 + 9)], fill=INK, width=2)
    d.polygon([(x0 + 40, y0 + 1), (x0 + 54, y0 + 1), (x0 + 50, y0 + 10),
               (x0 + 36, y0 + 10)], fill=RED)
    d.line([(x0 + 70, y0 + 6), (x0 + 76, y0 + 12), (x0 + 88, y0 + 4)],
           fill=INK, width=3)


def icon_race(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PAPER)
    for r in range(3):
        for c in range(3):
            if (r + c) % 2 == 0:
                d.rectangle([x0 + 8 + c * 8, y0 + 3 + r * 6,
                             x0 + 16 + c * 8, y0 + 9 + r * 6], fill=INK)
    d.line([(x0 + 40, y0 + 6), (x0 + 92, y0 + 6)], fill=AMBER, width=2)
    d.line([(x0 + 44, y0 + 12), (x0 + 92, y0 + 12)], fill=AMBER, width=2)
    d.line([(x0 + 40, y0 + 18), (x0 + 88, y0 + 18)], fill=AMBER, width=2)


def icon_cricket(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PAPER)
    for sx in (34, 42, 50):
        d.rectangle([x0 + sx, y0 + 6, x0 + sx + 3, y0 + 18], fill=INK)
    d.rectangle([x0 + 34, y0 + 4, x0 + 53, y0 + 6], fill=INK)
    dot(d, x1 - 20, y0 + 12, 6, RED)


def icon_drone(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    cx, cy = x0 + 40, y0 + 12
    d.line([(cx - 12, cy - 7), (cx + 12, cy + 7)], fill=LIGHT, width=3)
    d.line([(cx - 12, cy + 7), (cx + 12, cy - 7)], fill=LIGHT, width=3)
    dot(d, cx, cy, 4, LIGHT)
    starburst(d, x1 - 16, y0 + 12, 8, 3, 8, RED)


def icon_flame(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.polygon([(x0 + 46, y0 + 21), (x0 + 34, y0 + 14), (x0 + 36, y0 + 7),
               (x0 + 42, y0 + 10), (x0 + 46, y0 + 2), (x0 + 52, y0 + 9),
               (x0 + 58, y0 + 6), (x0 + 60, y0 + 14)], fill=RED)
    d.polygon([(x0 + 46, y0 + 21), (x0 + 40, y0 + 15), (x0 + 43, y0 + 10),
               (x0 + 48, y0 + 13), (x0 + 52, y0 + 15)], fill=AMBER)


def icon_power(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.polygon([(x0 + 52, y0 + 2), (x0 + 38, y0 + 13), (x0 + 48, y0 + 13),
               (x0 + 42, y0 + 21), (x0 + 58, y0 + 9), (x0 + 48, y0 + 9)],
              fill=AMBER)


def icon_factory(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PANEL)
    d.rectangle([x0 + 16, y0 + 11, x0 + 62, y0 + 20], fill=INK)
    d.rectangle([x0 + 20, y0 + 3, x0 + 26, y0 + 11], fill=INK)
    d.polygon([(x0 + 30, y0 + 11), (x0 + 38, y0 + 5), (x0 + 46, y0 + 11)],
              fill=INK)
    starburst(d, x1 - 16, y0 + 10, 8, 3, 8, RED)


def icon_ship(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.line([(x0 + 8, y0 + 18), (x1 - 8, y0 + 18)], fill=(58, 58, 64), width=1)
    d.polygon([(x0 + 18, y0 + 10), (x0 + 62, y0 + 10), (x0 + 56, y0 + 17),
               (x0 + 24, y0 + 17)], fill=MIDGREY)
    d.rectangle([x0 + 36, y0 + 3, x0 + 40, y0 + 10], fill=MIDGREY)
    starburst(d, x1 - 16, y0 + 9, 8, 3, 8, RED)


def icon_cross(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.rectangle([x0 + 42, y0 + 3, x0 + 50, y0 + 20], fill=PAPER)
    d.rectangle([x0 + 34, y0 + 8, x0 + 58, y0 + 15], fill=PAPER)


def icon_dome(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PAPER)
    d.pieslice([x0 + 32, y0 + 3, x0 + 60, y0 + 19], 180, 360, fill=INK)
    d.rectangle([x0 + 28, y0 + 17, x0 + 64, y0 + 20], fill=INK)
    for cx in (36, 46, 56):
        d.rectangle([cx, y0 + 11, cx + 3, y0 + 17], fill=PAPER)


def icon_map(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=PAPER)
    for xx in (x0 + 24, x0 + 48):
        d.line([(xx, y0 + 3), (xx, y0 + 19)], fill=GREY, width=1)
    dot(d, x0 + 60, y0 + 9, 6, RED)
    d.polygon([(x0 + 54, y0 + 12), (x0 + 66, y0 + 12), (x0 + 60, y0 + 20)],
              fill=RED)
    dot(d, x0 + 60, y0 + 9, 2, PAPER)


def icon_passport(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=INK)
    d.rectangle([x0 + 36, y0 + 3, x0 + 60, y0 + 20], fill=PAPER,
                outline=INK, width=1)
    d.line([(x0 + 41, y0 + 7), (x0 + 55, y0 + 16)], fill=RED, width=2)
    d.line([(x0 + 55, y0 + 7), (x0 + 41, y0 + 16)], fill=RED, width=2)


ICONS = {
    "ballot": icon_ballot, "race": icon_race, "cricket": icon_cricket,
    "drone": icon_drone, "flame": icon_flame, "power": icon_power,
    "factory": icon_factory, "ship": icon_ship, "cross": icon_cross,
    "dome": icon_dome, "map": icon_map, "passport": icon_passport,
}


def fit_also(d, full, fnt_bold, max_w):
    """Wrap an ALSO item to at most 2 lines, measured in the bold face
    (the lead is drawn bold). If it still spills, drop the trailing
    source in parentheses, then trim words with an ellipsis."""
    lines = wrap(d, full, fnt_bold, max_w)
    if len(lines) > 2 and full.rstrip().endswith(")"):
        cut = full.rstrip()
        cut = cut[:cut.rfind("(")].rstrip()
        lines = wrap(d, cut, fnt_bold, max_w)
    while len(lines) > 2:
        words = " ".join(lines[:2]).split()
        words = words[:-1]
        lines = wrap(d, " ".join(words) + " …", fnt_bold, max_w)
    return lines[:2]


# ------------------------------------------------------------- the map
# Stylised continents from a small fixed point list (lon, lat).

CONTINENTS = [
    [(-168, 66), (-140, 70), (-120, 71), (-100, 69), (-80, 73), (-60, 66),
     (-55, 52), (-70, 44), (-75, 35), (-80, 26), (-85, 30), (-95, 29),
     (-105, 22), (-115, 30), (-125, 40), (-125, 49), (-140, 60),
     (-155, 58), (-168, 66)],
    [(-80, 9), (-75, 7), (-85, 12), (-90, 14), (-95, 16), (-100, 19),
     (-105, 20), (-95, 15), (-85, 11), (-80, 9)],
    [(-35, 5), (-50, 0), (-60, -5), (-70, -12), (-70, -22), (-60, -28),
     (-55, -35), (-65, -40), (-70, -50), (-68, -54), (-72, -40),
     (-75, -30), (-78, -18), (-80, -5), (-78, 2), (-70, 10), (-60, 8),
     (-50, 5), (-35, 5)],
    [(-10, 36), (-5, 36), (0, 38), (5, 38), (10, 37), (15, 40), (20, 40),
     (25, 40), (30, 36), (28, 42), (20, 45), (12, 45), (5, 48), (0, 48),
     (-2, 50), (-5, 50), (-8, 48), (-10, 43), (-10, 36)],
    [(30, 36), (35, 36), (40, 40), (45, 42), (50, 40), (55, 42), (60, 45),
     (65, 50), (70, 55), (80, 60), (90, 62), (100, 60), (110, 58),
     (120, 60), (130, 58), (140, 60), (150, 60), (160, 62), (170, 66),
     (178, 65), (170, 60), (160, 55), (150, 45), (140, 40), (135, 35),
     (127, 33), (120, 30), (110, 20), (105, 10), (100, 8), (95, 15),
     (90, 22), (80, 15), (75, 10), (70, 20), (60, 25), (55, 25),
     (50, 29), (45, 30), (40, 30), (35, 30), (30, 31), (30, 36)],
    [(35, 30), (42, 28), (48, 25), (52, 15), (48, 12), (44, 12), (40, 15),
     (38, 20), (35, 25), (32, 30), (35, 30)],
    [(32, 0), (35, -5), (40, -10), (42, -15), (40, -20), (38, -25),
     (35, -30), (30, -28), (28, -20), (25, -15), (20, -10), (15, -5),
     (12, 0), (10, 5), (15, 8), (20, 10), (25, 5), (30, 0), (32, 0)],
    [(15, -20), (18, -25), (20, -30), (25, -35), (28, -28), (30, -22),
     (32, -18), (30, -15), (25, -15), (20, -17), (15, -20)],
    [(115, -12), (125, -15), (135, -12), (142, -11), (150, -20),
     (153, -27), (150, -37), (140, -38), (130, -32), (122, -34),
     (115, -32), (113, -22), (115, -12)],
]

# story number -> (lon, lat, dx nudge, dy nudge). The Europe / Middle
# East cluster is nudged apart so no two pins overlap.
PINS = {
    1: (30, 38, -16, 2), 2: (31, 50, 10, -6), 3: (20, 32, -14, 14),
    4: (114, 22, 0, 0), 5: (-115, 36, 0, 0), 6: (175, -41, 0, 0),
    7: (32, 15, -12, 10), 8: (34, 31, 0, 0), 9: (51, 35, 12, -10),
    10: (106, -6, 0, 0), 11: (24, 60, 0, -12), 12: (-48, -16, 0, 0),
    13: (12, 42, -12, -8), 14: (30, 13, 10, 16), 15: (33, 35, 12, -4),
}


def draw_map(d, x0, y0, x1, y1):
    d.rectangle([x0, y0, x1, y1], fill=(232, 226, 208))
    d.rectangle([x0, y0, x1, y1], outline=INK, width=1)
    spaced(d, x0 + 6, y0 + 5, "WHERE IT HAPPENED — PINS MATCH NUMBERS",
           font(SANS_B, 8), INK, 0)
    mx0, my0 = x0 + 6, y0 + 20
    mw, mh = (x1 - x0) - 12, (y1 - y0) - 26

    def xy(lon, lat):
        return (mx0 + (lon + 180) / 360 * mw,
                my0 + (90 - lat) / 170 * mh)

    for poly in CONTINENTS:
        d.polygon([xy(lon, lat) for lon, lat in poly], fill=TAN)
    fnt = font(SANS_B, 7)
    for num, (lon, lat, dx, dy) in sorted(PINS.items()):
        px, py = xy(lon, lat)
        px += dx
        py += dy
        dot(d, px, py, 6, RED)
        d.text((px, py), str(num), font=fnt, fill=(255, 255, 255),
               anchor="mm")


# ------------------------------------------------------------- layout

def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    marks = {}

    def mark(name, y):
        marks[name] = y
        return y

    # --- nameplate masthead: the paper's name, centred, black on paper
    y = 12
    centre(d, W // 2, y, "THE WORLD IN ONE DAY", font(SERIF_B, 38), INK)
    y = 54
    # dateline row: the day, in red spaced caps, left; the count, right
    spaced(d, M, y, "SUNDAY 22 NOVEMBER 2026", font(SANS_B, 11), RED, 1)
    right = "30 STORIES · 7 REGIONS · EVERY ONE DATED"
    spaced(d, W - M - spaced_w(d, right, font(SANS_B, 11), 1), y, right,
           font(SANS_B, 11), INK, 1)
    # 3px double rule under the masthead
    y = 70
    d.rectangle([M, y, W - M, y + 2], fill=INK)
    d.line([(M, y + 5), (W - M, y + 5)], fill=INK, width=1)
    mark("masthead", y + 6)

    # --- numbers strip: black serif figures, spaced-caps labels,
    #     1px vertical rules between the six cells
    y = 80
    cell = CW // 6
    for i, (num, label) in enumerate(NUMBERS):
        cx = M + i * cell + cell // 2
        centre(d, cx, y, num, font(SERIF_B, 24), INK)
        lw = spaced_w(d, label, font(SANS_B, 8), 1)
        spaced(d, cx - lw / 2, y + 27, label, font(SANS_B, 8), INK, 1)
        if i:
            d.line([(M + i * cell, y), (M + i * cell, y + 40)], fill=GREY,
                   width=1)
    y += 40
    mark("numbers", y)

    # --- region bar (colours kept: they are the proven navigation)
    y += 4
    rx = M
    for name, count, colour in REGIONS:
        w = int(round(count / 30 * CW))
        d.rectangle([rx, y, rx + w - 1, y + 15], fill=colour)
        centre(d, rx + w // 2, y + 3, "%s %d" % (name, count),
               font(SANS_B, 9), (255, 255, 255))
        rx += w
    y += 16
    mark("regions", y)

    # --- the day in UTC: paper strip, hairline rules, red label
    y += 4
    d.line([(M, y), (W - M, y)], fill=INK, width=1)
    y += 3
    tx = M
    tx += spaced(d, tx, y, "THE DAY IN UTC", font(SANS_B, 10), RED, 1) + 14
    for item in ("OVERNIGHT  186 drones fired at Ukraine",
                 "03:00 GMT  COP31 objections close",
                 "06:00 GMT  COP31 closing plenary"):
        w = d.textlength(item, font=font(SANS, 10))
        d.text((tx, y), item, font=font(SANS, 10), fill=INK)
        tx += w + 18
    y += 12
    d.line([(M, y), (W - M, y)], fill=INK, width=1)
    y += 3
    mark("utc", y)

    # --- hero zone on the 6-column grid: lead spans cols 1-4,
    #     the two secondaries stack in cols 5-6
    hero_y = y
    lead_x0, lead_x1 = M, M + 4 * COL + 3 * GUT        # 17 .. 673
    sec_x0, sec_x1 = lead_x1 + GUT, W - M               # 685 .. 1007

    # LEAD — COP31, the dominant story
    ax0, ay0, ax1, ay1 = lead_x0, hero_y, lead_x1, hero_y + 130
    art_cop31(d, ax0, ay0, ax1, ay1)
    d.rectangle([ax0, ay0, ax1, ay1], outline=INK, width=1)
    tag(d, ax1 - 4, ay0 + 5, HERO_LEAD["tag"], HERO_LEAD["tag"])
    d.rectangle([ax0 + 5, ay0 + 5, ax0 + 23, ay0 + 19], fill=PAPER)
    centre(d, ax0 + 14, ay0 + 6, HERO_LEAD["num"], font(SANS_B, 11), INK)
    y = ay1 + 6
    spaced(d, lead_x0, y, HERO_LEAD["kicker"], font(SANS_B, 10), RED, 1)
    y += 15
    for line in wrap(d, HERO_LEAD["headline"], font(SERIF_B, 38),
                     lead_x1 - lead_x0):
        d.text((lead_x0, y), line, font=font(SERIF_B, 38), fill=INK)
        y += 44
    y += 2
    for line in wrap(d, HERO_LEAD["body"], font(SANS, 11),
                     lead_x1 - lead_x0):
        d.text((lead_x0, y), line, font=font(SANS, 11), fill=INK)
        y += 13
    y += 3
    d.text((lead_x0, y), HERO_LEAD["source"], font=font(SANS, 9), fill=GREY)
    y += 15
    # pull-quote: red rule, red serif line
    d.rectangle([lead_x0, y, lead_x0 + 3, y + 16], fill=RED)
    d.text((lead_x0 + 10, y + 1), HERO_LEAD["quote"],
           font=font(SERIF_B, 13), fill=RED)
    lead_end = y + 18
    mark("lead", lead_end)

    # SECONDARIES, stacked in cols 5-6
    sec_y = hero_y
    sec_ends = []
    for hero, art in ((HERO_2, art_ukraine), (HERO_3, art_benghazi)):
        ax0, ay0, ax1, ay1 = sec_x0, sec_y, sec_x1, sec_y + 48
        art(d, ax0, ay0, ax1, ay1)
        d.rectangle([ax0, ay0, ax1, ay1], outline=INK, width=1)
        tag(d, ax1 - 4, ay0 + 5, hero["tag"], hero["tag"])
        d.rectangle([ax0 + 4, ay0 + 4, ax0 + 20, ay0 + 18], fill=PAPER)
        centre(d, ax0 + 12, ay0 + 5, hero["num"], font(SANS_B, 10), INK)
        y = ay1 + 6
        spaced(d, sec_x0, y, hero["kicker"], font(SANS_B, 9), RED, 1)
        y += 13
        for line in wrap(d, hero["headline"], font(SERIF_B, 17),
                         sec_x1 - sec_x0):
            d.text((sec_x0, y), line, font=font(SERIF_B, 17), fill=INK)
            y += 21
        y += 1
        for line in wrap(d, hero["body"], font(SANS, 10),
                         sec_x1 - sec_x0):
            d.text((sec_x0, y), line, font=font(SANS, 10), fill=INK)
            y += 12
        y += 2
        d.text((sec_x0, y), hero["source"], font=font(SANS, 9), fill=GREY)
        sec_y = y + 13
        sec_ends.append(y + 2)
    hero_end = max(lead_end, sec_ends[-1])
    # 1px vertical rule between the lead and the secondary columns
    d.line([(lead_x1 + GUT // 2, hero_y),
            (lead_x1 + GUT // 2, hero_end)], fill=GREY, width=1)
    mark("heroes", hero_end)
    y = hero_end + 6

    # --- minis header
    d.line([(M, y), (W - M, y)], fill=INK, width=1)
    y += 3
    spaced(d, M, y, "THE DAY IN BRIEF — TWELVE MORE STORIES",
           font(SANS_B, 11), INK, 1)
    y += 12
    mark("minis header", y)

    # --- minis: 4 columns, 1px vertical rules between them
    mcol, mgap, mrow = 240, 10, 82
    minis_top = y
    for row in range(3):
        for col in range(4):
            num, kicker, headline, body, tg, icon = MINIS[row * 4 + col]
            mx = M + col * (mcol + mgap)
            my = y + row * mrow
            ix0, iy0, ix1, iy1 = mx, my, mx + mcol, my + 20
            ICONS[icon](d, ix0, iy0, ix1, iy1)
            d.rectangle([ix0, iy0, ix1, iy1], outline=INK, width=1)
            tag(d, ix1 - 4, iy0 + 3, tg, tg)
            d.rectangle([ix0 + 3, iy0 + 3, ix0 + 19, iy0 + 17], fill=PAPER)
            centre(d, ix0 + 11, iy0 + 4, num, font(SANS_B, 10), INK)
            spaced(d, mx, my + 22, kicker, font(SANS_B, 9), RED, 1)
            hy = my + 33
            for line in wrap(d, headline, font(SERIF_B, 12), mcol):
                d.text((mx, hy), line, font=font(SERIF_B, 12), fill=INK)
                hy += 13
            by = my + 60
            for line in wrap(d, body, font(SANS, 10), mcol):
                d.text((mx, by), line, font=font(SANS, 10), fill=INK)
                by += 11
    for col in range(1, 4):
        vx = M + col * (mcol + mgap) - mgap // 2
        d.line([(vx, minis_top), (vx, minis_top + 3 * mrow)], fill=GREY,
               width=1)
    y = minis_top + 3 * mrow
    mark("minis", y)

    # --- also header
    y += 6
    d.line([(M, y), (W - M, y)], fill=INK, width=1)
    y += 3
    spaced(d, M, y, "ALSO ON SUNDAY 22 NOVEMBER — 15 MORE STORIES",
           font(SANS_B, 11), INK, 1)
    y += 12
    mark("also header", y)

    # --- also list (2 columns) + world map panel (1px box)
    block_y = y
    map_x0, map_x1 = M, M + 240
    ax0 = map_x1 + 14
    acol_w = (W - M - ax0 - 12) // 2
    cols = [ALSO[:8], ALSO[8:]]
    col_lines = []
    for items in cols:
        lines = []
        for num, lead, detail in items:
            full = "%s %s — %s" % (num, lead, detail)
            lines += fit_also(d, full, font(SANS_B, 10), acol_w)
        col_lines.append(lines)
    n_lines = max(len(c) for c in col_lines)
    block_h = n_lines * 11 + 4
    draw_map(d, map_x0, block_y, map_x1, block_y + block_h)
    for ci, lines in enumerate(col_lines):
        ax = ax0 + ci * (acol_w + 12)
        ay = block_y + 2
        for line in lines:
            if line is None:
                continue
            if line and line[0].isdigit() and " — " in line:
                num = line.split(" ", 1)[0]
                nw = d.textlength(num + " ", font=font(SANS_B, 10))
                d.text((ax, ay), num + " ", font=font(SANS_B, 10), fill=RED)
                lead_part, rest = line.split(" — ", 1)
                lead_txt = lead_part[len(num) + 1:]
                d.text((ax + nw, ay), lead_txt, font=font(SANS_B, 10),
                       fill=INK)
                lw = d.textlength(lead_txt, font=font(SANS_B, 10))
                d.text((ax + nw + lw, ay), " — " + rest,
                       font=font(SANS, 10), fill=INK)
            else:
                d.text((ax, ay), line, font=font(SANS, 10), fill=INK)
            ay += 11
    # hairline between the two ALSO columns
    vx = ax0 + acol_w + 6
    d.line([(vx, block_y), (vx, block_y + block_h)], fill=GREY, width=1)
    y = block_y + block_h + 6
    mark("also/map", y)

    # --- date check: red 1px box, sharp corners
    box_y = y
    d.rectangle([M, box_y, W - M, box_y + 40], outline=RED, width=1)
    chip = "DATE CHECK"
    fnt = font(SANS_B, 10)
    cw = int(d.textlength(chip, font=fnt)) + 10
    d.rectangle([M + 6, box_y + 6, M + 6 + cw, box_y + 22], fill=RED)
    d.text((M + 11, box_y + 8), chip, font=fnt, fill=(255, 255, 255))
    tx = M + 6 + cw + 8
    for line in wrap(d, DATE_CHECK, font(SANS, 10), W - M - 6 - tx):
        d.text((tx, box_y + 5), line, font=font(SANS, 10), fill=INK)
        box_y += 11
        if box_y > y + 29:
            break
    # second line of the date-check text sits under the chip row
    y = y + 40 + 6
    mark("date check", y)

    # --- footer: legend + sources, left-aligned
    lx = M
    lx += spaced(d, lx, y, "HOW TO READ THE TAGS — ", font(SANS_B, 10),
                 INK, 1) + 4
    lx += tag(d, lx + tag_w(d, "CONFIRMED"), y - 1, "CONFIRMED",
              "CONFIRMED") + 4
    d.text((lx, y), "official / 2+ outlets", font=font(SANS, 10), fill=INK)
    lx += d.textlength("official / 2+ outlets", font=font(SANS, 10)) + 8
    d.text((lx, y), "·", font=font(SANS, 10), fill=INK)
    lx += 10
    lx += tag(d, lx + tag_w(d, "REPORTED"), y - 1, "REPORTED",
              "REPORTED") + 4
    d.text((lx, y), "witnesses / one source", font=font(SANS, 10), fill=INK)
    lx += d.textlength("witnesses / one source", font=font(SANS, 10)) + 8
    d.text((lx, y), "·  CLAIM  one side’s claim, contested  ·  PENDING  not settled yet",
           font=font(SANS, 10), fill=INK)
    y += 14
    for line in wrap(d, SOURCES, font(SANS, 9), W - 2 * M):
        d.text((M, y), line, font=font(SANS, 9), fill=GREY)
        y += 11
    mark("legend/footer", y)

    # --- bottom: a 2px black rule closes the page
    y += 2
    d.rectangle([M, y, W - M, y + 1], fill=INK)
    y += 2
    mark("end", y)
    return img, marks


def main():
    img, marks = render()
    for name, y in marks.items():
        print("y %-14s %d" % (name, y))
    img.save("entry.png", format="PNG")
    import os
    size = os.path.getsize("entry.png")
    print("PNG bytes:", size)
    h1 = hashlib.sha256(open("entry.png", "rb").read()).hexdigest()
    img2, _ = render()
    img2.save("entry2.png", format="PNG")
    h2 = hashlib.sha256(open("entry2.png", "rb").read()).hexdigest()
    os.remove("entry2.png")
    print("sha256:", h1)
    print("second run identical:", h1 == h2)


if __name__ == "__main__":
    main()
