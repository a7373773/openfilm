
# -*- coding: utf-8 -*-
"""Scene-composition features from 1fps frames: sky / vegetation / water / warm-earth ratios."""
import os, json
import numpy as np
from PIL import Image

W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work"
FR = os.path.join(W, "analysis", "frames")
out = {}
for d in sorted(os.listdir(FR)):
    p = os.path.join(FR, d)
    if not os.path.isdir(p): continue
    recs = []
    for fn in sorted(os.listdir(p)):
        if not fn.endswith(".jpg"): continue
        try:
            t = int(fn.split("_")[1].split(".")[0]) - 1     # frames are 1-based, metrics 0-based
        except Exception:
            continue
        a = np.asarray(Image.open(os.path.join(p, fn)).convert("RGB")).astype(np.float32) / 255.0
        h, w, _ = a.shape
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        mx = a.max(axis=2); mn = a.min(axis=2)
        sat = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0)
        Y = 0.299 * R + 0.587 * G + 0.114 * B
        top = slice(0, max(1, int(h * 0.45)))
        # sky: bright, blue-leaning, low saturation variance, in the upper part
        sky = ((B > R + 0.02) & (Y > 0.42) & (sat < 0.55) & (B > G - 0.02))
        sky_frac = float(sky[top, :].mean())
        # vegetation: green dominant
        veg = (G > R + 0.015) & (G > B + 0.01)
        veg_frac = float(veg.mean())
        # water / haze blues anywhere
        wtr = (B > R + 0.03) & (sat > 0.05) & (Y > 0.15)
        wtr_frac = float(wtr.mean())
        # warm earth / sand / rock
        warm = (R > G + 0.02) & (G > B) & (Y > 0.25)
        warm_frac = float(warm.mean())
        # neutral gray construction / concrete / clothing
        neutral = (sat < 0.09) & (Y > 0.12)
        neutral_frac = float(neutral.mean())
        recs.append({"t": t, "sky": round(sky_frac, 4), "veg": round(veg_frac, 4),
                     "water": round(wtr_frac, 4), "warm": round(warm_frac, 4),
                     "neutral": round(neutral_frac, 4), "sat": round(float(sat.mean()), 4),
                     "Y": round(float(Y.mean()), 4)})
    out[d] = recs
json.dump(out, open(os.path.join(W, "analysis", "scene_feat.json"), "w"), ensure_ascii=False)
print("files", len(out), "frames", sum(len(v) for v in out.values()))
import itertools
allr = [r for v in out.values() for r in v]
def q(key):
    v = np.array([r[key] for r in allr])
    return {p: round(float(np.percentile(v, p)), 3) for p in (10, 25, 50, 75, 90)}
for k in ("sky", "veg", "water", "warm", "neutral"):
    print(k, q(k))
nat = np.array([r["sky"] + r["veg"] + r["water"] for r in allr])
print("nature(sky+veg+water) pct:", {p: round(float(np.percentile(nat, p)), 3) for p in (5, 10, 25, 50, 75, 90)})
print("frames with nature>=0.35:", int((nat >= 0.35).sum()), "/", len(nat))
