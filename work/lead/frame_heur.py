
# -*- coding: utf-8 -*-
"""Quick occlusion heuristics on extracted 1fps frames: skin fraction + hue concentration."""
import os, json, numpy as np
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
        t = int(fn.split("_")[1].split(".")[0])
        im = Image.open(os.path.join(p, fn)).convert("RGB")
        a = np.asarray(im).astype(np.float32)
        R, G, B = a[...,0], a[...,1], a[...,2]
        Y  = 0.299*R + 0.587*G + 0.114*B
        Cb = -0.1687*R - 0.3313*G + 0.5*B + 128
        Cr = 0.5*R - 0.4187*G - 0.0813*B + 128
        skin = (Cb >= 77) & (Cb <= 127) & (Cr >= 133) & (Cr <= 173) & (Y > 40)
        skinf = float(skin.mean())
        # hue concentration: how much of the frame sits in a single 30-degree hue bin among saturated pixels
        mx = a.max(axis=2); mn = a.min(axis=2)
        sat = (mx - mn) / (mx + 1e-6)
        hs = sat > 0.25
        if hs.sum() > 50:
            rr, gg, bb = R[hs], G[hs], B[hs]
            h = np.zeros_like(rr)
            m = (mx[hs] == rr); h[m] = ((gg[m]-bb[m])/(mx[hs][m]-mn[hs][m]+1e-6)) % 6
            m = (mx[hs] == gg) & ~m; h[m] = (bb[m]-rr[m])/(mx[hs][m]-mn[hs][m]+1e-6) + 2
            m2 = (mx[hs] == bb) & ~((mx[hs]==rr)|(mx[hs]==gg)); h[m2] = (rr[m2]-gg[m2])/(mx[hs][m2]-mn[hs][m2]+1e-6) + 4
            h = (h * 60) % 360
            hist, _ = np.histogram(h, bins=12, range=(0,360))
            conc = float(hist.max() / max(1, hist.sum()))
        else:
            conc = 0.0
        # gray/low-sat dominance
        lowsat = float((sat < 0.08).mean())
        recs.append({"t": t, "skinf": round(skinf,4), "hueconc": round(conc,4),
                     "lowsat": round(lowsat,4), "satmean": round(float(sat.mean()),4)})
    out[d] = recs
json.dump(out, open(os.path.join(W, "analysis", "frame_heuristics.json"), "w"), ensure_ascii=False)
print("files", len(out), "frames", sum(len(v) for v in out.values()))
# report suspicious
print("\n=== frames with skin fraction > 0.25 ===")
for d, recs in out.items():
    hi = [r for r in recs if r["skinf"] > 0.25]
    if hi: print("%-20s %d frames: %s" % (d, len(hi), [r["t"] for r in hi][:40]))
print("\n=== frames with hue concentration > 0.75 ===")
for d, recs in out.items():
    hi = [r for r in recs if r["hueconc"] > 0.75]
    if hi: print("%-20s %d frames: %s" % (d, len(hi), [r["t"] for r in hi][:40]))
