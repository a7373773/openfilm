# -*- coding: utf-8 -*-
"""01_index: probe + aspect gate + per-frame stats + subject clustering.
usage: python 01_index.py <clip_dir> <workdir>"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

SRC = sys.argv[1]; WORK = sys.argv[2]
FR = os.path.join(WORK, "frames")
files = sorted(f for f in os.listdir(SRC) if f.upper().endswith((".MP4", ".MOV")))
os.makedirs(FR, exist_ok=True)

clips = []
for f in files:
    d = probe(os.path.join(SRC, f))
    d["aspect"] = aspect_class(d)
    extract_frames(os.path.join(SRC, f), os.path.join(FR, os.path.splitext(f)[0]))
    rows = []
    for jpg in sorted(os.listdir(os.path.join(FR, os.path.splitext(f)[0]))):
        p = os.path.join(FR, os.path.splitext(f)[0], jpg)
        img = imread_u(p)
        if img is None: continue
        r = frame_stats(img)
        r["t"] = jpg.replace(".jpg", "")
        rows.append(r)
    d["n"] = len(rows)
    if rows:
        d["sharp"] = float(np.median([r["sharp"] for r in rows]))
        d["bright"] = float(np.median([r["bright"] for r in rows]))
        d["sat"] = float(np.median([r["sat"] for r in rows]))
        d["hist"] = np.mean([r["hist"] for r in rows], axis=0).tolist()
        d["quality"] = quality_score(rows)
        # faces every 4th frame (cheap)
        fc, fa = [], []
        for r in rows[::4]:
            img = imread_u(os.path.join(FR, os.path.splitext(f)[0], r["t"] + ".jpg"))
            if img is None: continue
            n, area = faces(img)
            fc.append(n); fa.append(area)
        d["faces"] = float(np.mean(fc)) if fc else 0.0
        d["face_area"] = float(np.mean(fa)) if fa else 0.0
        d["rows"] = [{"t": r["t"], "sharp": round(r["sharp"], 1), "bright": round(r["bright"], 1)} for r in rows]
    # rejection reasons (aspect / rotation / quality)
    why = []
    if d["aspect"] != "landscape": why.append("非横屏(%s, rot=%.0f)" % (d["aspect"], d.get("rot", 0)))
    if d.get("w", 1920) != RULES["aspect"]["target"][0] or d.get("h", 1080) != RULES["aspect"]["target"][1]:
        why.append("尺寸 %sx%s" % (d.get("w"), d.get("h")))
    if d.get("sharp", 0) < RULES["quality"]["min_sharp"] and d.get("sat", 0) > 40: why.append("锐度 %.0f 偏低" % d.get("sharp", 0))
    if d.get("bright", 0) > RULES["quality"]["max_bright"]: why.append("亮度 %.0f 过曝" % d.get("bright", 0))
    d["reject"] = why
    clips.append(d)
    print("%-12s %s dur=%5.2f sh=%6.0f br=%3.0f faces=%.1f q=%5.1f %s" % (
        f, d["aspect"][:9], d.get("dur", 0), d.get("sharp", 0), d.get("bright", 0),
        d.get("faces", 0), d.get("quality", 0), ("REJECT: " + " / ".join(why)) if why else ""))

# ---- subject clustering by colour-histogram distance (greedy) ----
usable = [c for c in clips if not c["reject"] and "hist" in c]
usable.sort(key=lambda c: c["tc_sec"])
clusters = []
for c in usable:
    for cl in clusters:
        if hist_dist(c["hist"], cl["mean"]) < RULES["dedupe"]["cluster_threshold"]:
            cl["members"].append(c)
            cl["mean"] = np.mean([m["hist"] for m in cl["members"]], axis=0).tolist()
            break
    else:
        clusters.append({"id": len(clusters), "mean": c["hist"], "members": [c]})

print("\n=== clusters (%d) ===" % len(clusters))
for cl in clusters:
    cl["members"].sort(key=lambda m: -m["quality"])
    best = cl["members"][0]
    print("C%02d n=%d  best=%s q=%.1f faces=%.1f dur=%.2f | %s" % (
        cl["id"], len(cl["members"]), best["file"], best["quality"], best["faces"], best["dur"],
        ", ".join(m["file"].replace(".MP4", "") for m in cl["members"])))

out = dict(src=SRC, clips=[{k: v for k, v in c.items() if k != "hist"} | {"hist": c.get("hist", [])} for c in clips],
           clusters=[{"id": cl["id"], "members": [m["file"] for m in cl["members"]],
                      "best": cl["members"][0]["file"], "n": len(cl["members"])} for cl in clusters])
json.dump(out, open(os.path.join(WORK, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nportrait/rotated rejected:", [c["file"] for c in clips if c["aspect"] != "landscape"])
