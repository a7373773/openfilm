# -*- coding: utf-8 -*-
"""Octave/fine-detail test: lapvar at 480 vs at 240 to see if low 'sharp' is真糊 or just低细节内容."""
import os, sys, json, math
sys.path.insert(0, "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/scripts")
import numpy as np
from PIL import Image
FR = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/frames"
def lapvar(g):
    p = np.pad(g,1,mode="edge")
    lap = p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:]-4.0*g
    return float(lap.var())
def octave(fn, t):
    im = Image.open(os.path.join(FR, fn, "sec_%04d.jpg" % (t+1))).convert("L")
    g = np.asarray(im, dtype=np.float32)
    g2 = np.asarray(im.resize((240,135), Image.LANCZOS), dtype=np.float32)
    L1 = lapvar(g); L2 = lapvar(g2)
    return L1, L2, L1/max(4.0*L2, 1e-6)
for fn in ("REC-0007-A","REC-0001-A","REC-0005-A","REC-0013-A","REC-0017-A","REC-0006-A"):
    D = json.load(open("D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/parts/%s.json" % fn, encoding="utf-8"))
    fr = D["frames"]
    print("=== %s ===" % fn)
    for t in range(0, min(len(fr),120), 6):
        L1,L2,R = octave(fn, t)
        print("  t=%3d sharp480=%7.0f ratio=%5.2f  (L480=%.0f L240=%.0f)" % (t, fr[t]["sharp"], R, L1, L2))
