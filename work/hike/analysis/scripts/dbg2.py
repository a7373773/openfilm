# -*- coding: utf-8 -*-
import os, json, math, itertools
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
H = os.path.join(OUT, "hashes"); M = json.load(open(os.path.join(OUT,"metrics.json"),encoding="utf-8"))
def load(stem): return json.load(open(os.path.join(H, stem+".json"), encoding="utf-8"))
def pc(x):
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return (x * np.uint64(0x0101010101010101)) >> np.uint64(56)
def mats(A,B):
    da=np.array([f["dhash"] for f in A["frames"]],dtype=np.uint64); db=np.array([f["dhash"] for f in B["frames"]],dtype=np.uint64)
    DH=pc(np.bitwise_xor(da[:,None],db[None,:])).astype(np.int16)
    ha=np.array([f["hist"] for f in A["frames"]]); hb=np.array([f["hist"] for f in B["frames"]])
    ha/=np.maximum(np.linalg.norm(ha,axis=1,keepdims=True),1e-9); hb/=np.maximum(np.linalg.norm(hb,axis=1,keepdims=True),1e-9)
    return DH, ha@hb.T
def relaxed(A,B,T1,T2):
    DH,COS=mats(A,B); m=(DH<=T1)&(COS>=T2)
    covA=m.any(axis=1).mean(); covB=m.any(axis=0).mean()
    return float(min(covA,covB)), float(np.median(DH[m])) if m.any() else None, float(covA), float(covB)
stems=sorted(x[:-5] for x in os.listdir(H) if x.endswith(".json"))
scene=json.load(open(os.path.join(OUT,"scene_similar.json"),encoding="utf-8"))
print("=== relaxed cover (dh<=14, cos>=0.90) for scene-similar pairs, sorted ===")
rows=[]
for s in scene:
    A=load(s["A"].replace(".mp4","")); B=load(s["B"].replace(".mp4",""))
    c,md,ca,cb=relaxed(A,B,14,0.90)
    c2,md2,ca2,cb2=relaxed(A,B,10,0.93)
    rows.append((c,c2,s["A"],s["B"],s["hist_cos"],s["luma_diff"],s["adjacent"],md,md2))
rows.sort(key=lambda r:-r[0])
for r in rows[:25]:
    print("  cover14=%.2f cover10=%.2f %-13s %-13s sceneCos=%.3f dLuma=%.0f adj=%s medDH14=%.0f medDH10=%.0f" % (
        r[0],r[1],r[2].replace(".mp4",""),r[3].replace(".mp4",""),r[4],r[5],r[6],r[7] or 0,r[8] or 0))
print()
def detail(sa,sb,label):
    A=load(sa); B=load(sb)
    print("=== %s : %s (%d fr, %.2fs) vs %s (%d fr, %.2fs) ===" % (label, sa, len(A["frames"]), A["duration"], sb, len(B["frames"]), B["duration"]))
    print("  t      | A: luma sharp fr edge diff sky  green | B: luma sharp fr edge diff sky  green")
    n=max(len(A["frames"]),len(B["frames"]))
    for i in range(n):
        a=A["frames"][i] if i<len(A["frames"]) else None
        b=B["frames"][i] if i<len(B["frames"]) else None
        fa=M[sa][i] if i<len(M[sa]) else None
        fb=M[sb][i] if i<len(M[sb]) else None
        def fmt(fh,fm):
            if fh is None or fm is None: return " "*44
            return "%4.0f %5.0f %.2f %.2f %4.1f %.2f %.2f" % (fm["luma"],fm["sharp"],fm["fineratio"],fm["edgefrac"],fm["diff"],fh["sky"],fh["green"])
        print("  %5.1f | %s | %s" % (i*0.5, fmt(a,fa), fmt(b,fb)))
    c,md,ca,cb=relaxed(A,B,14,0.90); c2,md2,_,_=relaxed(A,B,10,0.93); c3,md3,_,_=relaxed(A,B,8,0.95)
    print("  relaxed cover: (14/.90)=%.2f medDH=%.1f | (10/.93)=%.2f | (8/.95)=%.2f" % (c,md or 0,c2,c3))
    # series correlation of sky/green/luma
    for k in ("sky","green"):
        x=np.array([f[k] for f in A["frames"]]); y=np.array([f[k] for f in B["frames"]])
        nn=min(len(x),len(y))
        if nn>3: print("  series corr(%s) = %.3f" % (k, float(np.corrcoef(x[:nn],y[:nn])[0,1])))
print()
detail("C1897S03","C1898S03","lead-suspect-1")
detail("C1843S03","C1844S03","lead-suspect-2")
detail("C1827S03","C1828S03","found-dup")
detail("C1874S03","C1875S03","scene-adjacent")
