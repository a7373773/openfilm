# -*- coding: utf-8 -*-
import os, json, math, glob
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
H = os.path.join(OUT, "hashes")
def load(fn):
    return json.load(open(os.path.join(H, fn.replace(".mp4","") + ".json"), encoding="utf-8"))
def ham(a,b): return bin(a^b).count("1")
def cos(u,v):
    d=sum(x*y for x,y in zip(u,v)); nu=math.sqrt(sum(x*x for x in u)); nv=math.sqrt(sum(y*y for y in v))
    return d/max(nu*nv,1e-9)
def pair_detail(fa, fb, name):
    A=load(fa); B=load(fb)
    print("=== %s (%d frames, %.2fs)  vs  %s (%d frames, %.2fs) ===" % (
        fa, len(A["frames"]), A["duration"], fb, len(B["frames"]), B["duration"]))
    mins=[]
    for a in A["frames"]:
        best=None
        for b in B["frames"]:
            dh=ham(a["dhash"],b["dhash"]); c=cos(a["hist"],b["hist"])
            sc=dh+12*(1-c)
            if best is None or sc<best[0]: best=(sc,dh,c,b["t"])
        mins.append(best)
        print("  tA=%5.1f  best tB=%5.1f dh=%2d cos=%.4f" % (a["t"], best[3], best[1], best[2]))
    dhs=[m[1] for m in mins]; css=[m[2] for m in mins]
    print("  median dh=%.1f  median cos=%.4f  frac(dh<=8 & cos>=0.92)=%.2f" % (
        sorted(dhs)[len(dhs)//2], sorted(css)[len(css)//2],
        np.mean([1.0 if (m[1]<=8 and m[2]>=0.92) else 0.0 for m in mins])))
    # global mean histogram similarity
    ha=np.mean([a["hist"] for a in A["frames"]],axis=0); hb=np.mean([b["hist"] for b in B["frames"]],axis=0)
    print("  clip-mean hist cos = %.4f" % cos(ha,hb))
    for k in ("sky","green","warm"):
        print("  %s: A mean %.3f  B mean %.3f" % (k, np.mean([a[k] for a in A["frames"]]), np.mean([b[k] for b in B["frames"]])))
    with open(os.path.join(OUT,"metrics.json"),encoding="utf-8") as fh: M=json.load(fh)
    for fn in (fa, fb):
        fr=M[fn]
        print("  %s metrics: luma %.0f sharp %.0f fr %.3f edge %.2f diff %.1f" % (fn,
          np.mean([f["luma"] for f in fr]), np.mean([f["sharp"] for f in fr]),
          np.mean([f["fineratio"] for f in fr]), np.mean([f["edgefrac"] for f in fr]),
          np.mean([f["diff"] for f in fr])))
    print()
pair_detail("C1897S03.mp4","C1898S03.mp4","1897/1898")
pair_detail("C1843S03.mp4","C1844S03.mp4","1843/1844")
pair_detail("C1905S03.mp4","C1906S03.mp4","1905/1906")
