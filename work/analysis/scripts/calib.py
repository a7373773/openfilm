# -*- coding: utf-8 -*-
"""Calibration: does fineratio separate TRUE defocus from low-texture-but-sharp content?"""
import os, sys, json
sys.path.insert(0, "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/scripts")
import numpy as np
from PIL import Image, ImageFilter
FR = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/frames"

def lapvar(g):
    p = np.pad(g, 1, mode="edge")
    lap = p[:-2,1:-1] + p[2:,1:-1] + p[1:-1,:-2] + p[1:-1,2:] - 4.0*g
    return float(lap.var())

def metrics(im):
    g = np.asarray(im.convert("L"), dtype=np.float32)
    lv = lapvar(g)
    g2 = np.asarray(im.convert("L").resize((240,135), Image.LANCZOS), dtype=np.float32)
    lv2 = lapvar(g2)
    fr = lv / max(4.0*lv2, 1e-6)
    p = np.pad(g,1,mode="edge")
    gx = (p[:-2,2:] + 2*p[1:-1,2:] + p[2:,2:]) - (p[:-2,:-2] + 2*p[1:-1,:-2] + p[2:,:-2])
    gy = (p[2:,:-2] + 2*p[2:,1:-1] + p[2:,2:]) - (p[:-2,:-2] + 2*p[:-2,1:-1] + p[:-2,2:])
    mag = np.sqrt(gx*gx+gy*gy)
    return lv, fr, float(np.mean(mag > 30.0)), float(g.std())

def load(fn, t):
    return Image.open(os.path.join(FR, fn, "sec_%04d.jpg" % (t+1))).convert("RGB")

rows = []
print("--- TRUE DEFOCUS: sharp frame + gaussian blur ---")
for fn, t, tag in (("REC-0013-A", 24, "sharp-ref"), ("REC-0017-A", 54, "sharp-ref"), ("REC-0021-A", 76, "sharp-warm")):
    base_im = load(fn, t)
    for sigma in (0, 1.0, 1.5, 2.0, 3.0):
        im = base_im if sigma == 0 else base_im.filter(ImageFilter.GaussianBlur(sigma))
        lv, fr, ef, sd = metrics(im)
        print("%-12s t=%3d sigma=%.1f | sharp=%7.1f fineratio=%.3f edgefrac=%.3f lumastd=%5.1f" % (fn, t, sigma, lv, fr, ef, sd))
print()
print("--- LOW-TEXTURE / bright uniform (sky, water, haze) ---")
for fn, t, tag in (("REC-0027-A",10,"bright sky uni0.62"), ("REC-0025-A",16,"flat uni0.49"), ("REC-0025-A",28,"flat uni0.45"),
                   ("REC-0024-A",105,"flat uni0.49"), ("REC-0024-A",101,"flat uni0.40"), ("REC-0027-A",39,"sky/dark"),
                   ("REC-0020-A",17,"uni0.29"), ("REC-0013-A",46,"dark uni0.36")):
    lv, fr, ef, sd = metrics(load(fn, t))
    print("%-12s t=%3d %-20s | sharp=%7.1f fineratio=%.3f edgefrac=%.3f lumastd=%5.1f" % (fn, t, tag, lv, fr, ef, sd))
print()
print("--- FLAGGED SOFT FRAMES in 'blurry' files (what we labelled BLUR) ---")
for fn, t in (("REC-0007-A",66), ("REC-0007-A",19), ("REC-0003-A",40), ("REC-0003-A",44), ("REC-0002-A",5),
              ("REC-0006-A",60), ("REC-0006-A",110), ("REC-0001-A",24), ("REC-0008-A",72), ("REC-0004-A",4),
              ("REC-0005-A",2), ("REC-0008-A",14)):
    lv, fr, ef, sd = metrics(load(fn, t))
    print("%-12s t=%3d | sharp=%7.1f fineratio=%.3f edgefrac=%.3f lumastd=%5.1f" % (fn, t, lv, fr, ef, sd))
