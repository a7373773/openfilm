# -*- coding: utf-8 -*-
import os, json, math
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"),encoding="utf-8"))
meta = json.load(open(os.path.join(OUT,"meta.json"),encoding="utf-8"))
det = json.load(open(os.path.join(OUT,"mask_detail.json"),encoding="utf-8"))
H = os.path.join(OUT,"hashes")
def hs(fn): return json.load(open(os.path.join(H, fn.replace(".mp4","")+".json"),encoding="utf-8"))
BLOCKLBL=("BLACK","WHITE","BLOCK","BLUR")
print("%-14s %5s %5s %5s %6s %6s %6s %5s %5s" % ("file","dur","usable","blocked","sharp","finer","green","sky","luma"))
tot_usable=0.0; rows=[]
for fn in sorted(M):
    fr=M[fn]; n=len(fr)
    bad=set()
    for r in det[fn]["runs_all"]:
        if r["label"] in BLOCKLBL:
            a=int(round(r["start"]*2)); b=int(round(r["end"]*2))
            for t in range(a,b): bad.add(t)
    usable=[i for i in range(n) if i not in bad]
    hs_=hs(fn)
    g=float(np.mean([f["green"] for f in hs_["frames"]])) if hs_["frames"] else 0
    s=float(np.mean([f["sky"] for f in hs_["frames"]])) if hs_["frames"] else 0
    rows.append((fn, n*0.5, len(usable)*0.5, len(bad)*0.5,
                 float(np.mean([f["sharp"] for f in fr])), float(np.mean([f["fineratio"] for f in fr])), g, s,
                 float(np.mean([f["luma"] for f in fr])), usable))
    tot_usable += len(usable)*0.5
    print("%-14s %5.2f %5.1f %5.1f %6.0f %6.3f %6.2f %5.2f %5.0f" % (
        fn, n*0.5, len(usable)*0.5, len(bad)*0.5, rows[-1][4], rows[-1][5], g, s, rows[-1][8]))
print()
print("total duration %.1fs, usable %.1fs" % (sum(r[1] for r in rows), tot_usable))
good=[r for r in rows if r[2]>=2.0 and r[4]>=600]
print("clips with >=2s usable and sharp>=600:", len(good), " sum usable %.1fs" % sum(r[2] for r in good))
good2=[r for r in rows if r[2]>=2.0]
print("clips with >=2s usable:", len(good2), " sum usable %.1fs" % sum(r[2] for r in good2))
