# -*- coding: utf-8 -*-
"""Attach graphics overlays (title / lower thirds / stickers / progress / end card) to hike EDL."""
import json, os
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
edl = json.load(open(os.path.join(WK, "edl.json"), encoding="utf-8-sig"))
shots = edl["shots"]
starts, t = [], 0.0
for s in shots:
    starts.append(round(t, 3)); t += float(s["dur"]) - float(s.get("trans", 0.0) or 0.0)
TOTAL = round(t, 3)
secs = {}
for i, s in enumerate(shots):
    secs.setdefault(int(s["sec"]), []).append(i)
print("total %.2f  shots %d  sections %s" % (TOTAL, len(shots), {k: len(v) for k, v in secs.items()}))

ov = []
def add(png, start, dur, x=0, y=0, fade=0.45, **kw):
    d = dict(png=png, start=round(max(0.0, start), 2), dur=round(dur, 2), x=x, y=y, fade=fade)
    d.update(kw); ov.append(d)

def at(sec, frac):
    ids = secs.get(sec) or secs[min(secs)]
    k = min(len(ids) - 1, max(0, int(round(frac * (len(ids) - 1)))))
    return ids[k]

# title
add("01_title.png", 0.7, 5.6, fade=0.8)
# progress track + dot
add("09_bar_bg.png", 0.2, TOTAL, fade=0.3)
add("11_bar_dot.png", 0.0, TOTAL, fade=0.3, x_expr="120+1676*(t/TOTAL)", y=0)

CAPS = [
    ("lt_01.png", 0, 0.10, "出发"),
    ("lt_02.png", 1, 0.12, "身体先醒过来"),
    ("lt_03.png", 1, 0.66, "林间穿行"),
    ("lt_04.png", 2, 0.08, "最陡的一段"),
    ("lt_05.png", 2, 0.70, "补给时刻"),
    ("lt_06.png", 3, 0.12, "山脊之上"),
    ("lt_07.png", 4, 0.55, "登顶"),
]
for png, si, frac, label in CAPS:
    a = at(si, frac)
    st = starts[a] + 0.55
    add(png, st, 5.2, fade=0.4)
    print("  %-8s %6.1fs  shot %d" % (label, st, a))

STICK = [
    ("03_st_sun.png", 0, 0.10, 1.0),
    ("04_st_heart.png", 1, 0.12, 0.9),
    ("06_st_boot.png", 2, 0.08, 1.1),
    ("05_st_water.png", 2, 0.70, 1.0),
    ("07_st_flag.png", 4, 0.55, 0.8),
]
for png, si, frac, off in STICK:
    a = at(si, frac)
    add(png, starts[a] + off, 3.4, fade=0.35)

END_D = 5.8
add("08_endcard.png", TOTAL - END_D, END_D, fade=1.1)

edl["overlays"] = sorted(ov, key=lambda o: o["start"])
json.dump(edl, open(os.path.join(WK, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("overlays:", len(edl["overlays"]))
for o in edl["overlays"]: print("   %-18s %6.1f +%4.1f" % (o["png"], o["start"], o["dur"]))
