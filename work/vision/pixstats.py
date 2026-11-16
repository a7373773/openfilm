
# -*- coding: utf-8 -*-
"""Objective per-frame image stats used to cross-validate CLIP judgements."""
import json, os
import numpy as np
from PIL import Image

FRAMES = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\frames"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision\pixstats.json"

def stats(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0
    h, w, _ = a.shape
    r, g, b = a[:,:,0], a[:,:,1], a[:,:,2]
    gray = 0.299*r + 0.587*g + 0.114*b
    mean = float(gray.mean()); std = float(gray.std())
    lap = (-4.0*gray[1:-1,1:-1] + gray[1:-1,:-2] + gray[1:-1,2:] + gray[:-2,1:-1] + gray[2:,1:-1])
    lapvar = float(lap.var())
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = np.where(mx > 1e-6, (mx-mn)/np.maximum(mx, 1e-6), 0.0)
    rgb_ = np.dstack([r, g, b])
    satmean = float(sat.mean())
    rg = r - g; yb = 0.5*(r+g) - b
    colorful = float(np.sqrt(rg.std()**2 + yb.std()**2) + 0.3*np.sqrt(rg.mean()**2 + yb.mean()**2))
    dark = float((gray < 0.12).mean()); bright = float((gray > 0.9).mean())
    skin = (r > 0.35) & (g > 0.2) & (g < 0.85) & (b < 0.75) & (r > g+0.06) & (r > b+0.06)
    skinfrac = float(skin.mean())
    th = max(0.02, float(lap.std()))
    edge = float((np.abs(lap) > th).mean())

    # --- vertical structure: top vs bottom brightness / texture -----------------
    h3 = max(1, int(h*0.3))
    topMean = float(gray[:h3].mean()); botMean = float(gray[-h3:].mean())
    topLap = float(lap[:max(1,int(lap.shape[0]*0.3))].var()); botLap = float(lap[-max(1,int(lap.shape[0]*0.3)):].var())

    # --- sky fraction in the top 45% -------------------------------------------
    ht = max(1, int(h*0.45))
    tb = gray[:ht]; tr, tg, tbb = r[:ht], g[:ht], b[:ht]
    skym = ((tbb >= tr - 0.02) & (tb > 0.45)) | (tb > 0.80)
    skyfrac = float(skym.mean())

    # --- green vegetation fraction --------------------------------------------
    green = (g > r + 0.02) & (g > b + 0.02) & (g > 0.15)
    greenfrac = float(green.mean())

    # --- flat / featureless fraction (low local contrast in 8x8 blocks) --------
    gy, gx = gray.shape
    bh, bw = max(1, gy//16), max(1, gx//16)
    blocks = gray[:bh*16, :bw*16].reshape(bh, 16, bw, 16)
    bstd = blocks.std(axis=(1, 3))
    flatfrac = float((bstd < 0.02).mean())

    return dict(mean=mean, std=std, lapvar=lapvar, sat=satmean, colorful=colorful,
                dark=dark, bright=bright, skin=skinfrac, edge=edge,
                topMean=topMean, botMean=botMean, vertGrad=topMean-botMean,
                topLap=topLap, botLap=botLap, skyfrac=skyfrac,
                greenfrac=greenfrac, flatfrac=flatfrac, w=w, h=h)

def main():
    dirs = sorted(d for d in os.listdir(FRAMES) if os.path.isdir(os.path.join(FRAMES, d)))
    out = {}
    n = 0
    for d in dirs:
        dd = os.path.join(FRAMES, d)
        files = sorted(f for f in os.listdir(dd) if f.endswith(".jpg"))
        for f in files:
            try:
                out.setdefault(d, {})[str(int(f[4:8]))] = stats(os.path.join(dd, f))
            except Exception as e:
                print("ERR", d, f, e, flush=True)
            n += 1
        print(d, len(files), flush=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(out, fh)
    print("TOTAL", n, "->", OUT, flush=True)

main()
