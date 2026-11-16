# -*- coding: utf-8 -*-
import os, json, itertools
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
H = os.path.join(OUT,"hashes"); M = json.load(open(os.path.join(OUT,"metrics.json"),encoding="utf-8"))
def load(s): return json.load(open(os.path.join(H, s+".json"), encoding="utf-8"))
def pc(x):
    x = (x & np.uint64(0xFFFFFFFFFFFFFFFF))
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return int((x * np.uint64(0x0101010101010101) & np.uint64(0xFFFFFFFFFFFFFFFF)) >> np.uint64(56))
stems = sorted(x[:-5] for x in os.listdir(H) if x.endswith(".json"))
C = {s: load(s) for s in stems}
def meanhist(s):
    h=np.mean([f["hist"] for f in C[s]["frames"]],axis=0); return h/max(np.linalg.norm(h),1e-9)
MH={s:meanhist(s) for s in stems}
def mluma(s): return float(np.mean([f["luma"] for f in M[s+".mp4"]]))
MSKY={s:float(np.mean([f["sky"] for f in C[s]["frames"]])) for s in stems}
MGRN={s:float(np.mean([f["green"] for f in C[s]["frames"]])) for s in stems}
MLUM={s:mluma(s) for s in stems}
noise={}
rows=[]
for a,b in itertools.combinations(stems,2):
    cos=float(MH[a]@MH[b])
    if cos < 0.96: continue
    dl=abs(MLUM[a]-MLUM[b]); ds=abs(MSKY[a]-MSKY[b]); dg=abs(MGRN[a]-MGRN[b])
    if dl>10 or ds>0.06: continue
    rows.append((cos,dl,ds,dg,a,b))
rows.sort(key=lambda r:(-r[0],r[1]))
print("same-scene suspects (histcos>=0.96, |dLuma|<=10, |dSky|<=0.06):", len(rows))
for r in rows:
    print("  cos=%.4f dLuma=%4.0f dSky=%.3f dGreen=%.3f  %-10s %-10s  (luma %.0f/%.0f sky %.2f/%.2f green %.2f/%.2f)" % (
        r[0],r[1],r[2],r[3],r[4],r[5], MLUM[r[4]],MLUM[r[5]], MSKY[r[4]],MSKY[r[5]], MGRN[r[4]],MGRN[r[5]]))
