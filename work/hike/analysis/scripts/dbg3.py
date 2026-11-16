# -*- coding: utf-8 -*-
import os, json
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
H = os.path.join(OUT, "hashes"); M = json.load(open(os.path.join(OUT,"metrics.json"),encoding="utf-8"))
def load(s): return json.load(open(os.path.join(H, s+".json"), encoding="utf-8"))
def pc(x):
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return (x * np.uint64(0x0101010101010101)) >> np.uint64(56)
def ev(sa,sb):
    A=load(sa); B=load(sb)
    da=np.array([f["dhash"] for f in A["frames"]],dtype=np.uint64); db=np.array([f["dhash"] for f in B["frames"]],dtype=np.uint64)
    DH=pc(np.bitwise_xor(da[:,None],db[None,:])).astype(np.int16)
    ha=np.array([f["hist"] for f in A["frames"]]); hb=np.array([f["hist"] for f in B["frames"]])
    ha/=np.maximum(np.linalg.norm(ha,axis=1,keepdims=True),1e-9); hb/=np.maximum(np.linalg.norm(hb,axis=1,keepdims=True),1e-9)
    COS=ha@hb.T
    m=(DH<=10)&(COS>=0.93)
    print("%s(%d fr %.2fs) vs %s(%d fr %.2fs)" % (sa,len(A["frames"]),A["duration"],sb,len(B["frames"]),B["duration"]))
    print("  minDH=%.0f medDH_all=%.1f  maxCOS=%.4f  coverA10=%.2f coverB10=%.2f" % (
        DH.min(), np.median(DH), COS.max(), m.any(axis=1).mean(), m.any(axis=0).mean()))
    print("  best-match mapping A->B (tA -> tB, dh, cos):")
    for i,a in enumerate(A["frames"][:12]):
        j=int(np.argmin(DH[i])); print("    %4.1f -> %4.1f  dh=%2d cos=%.3f" % (a["t"], B["frames"][j]["t"], DH[i,j], COS[i,j]))
    print("  B frame-to-frame dhash deltas:", [int(pc(np.uint64(db[i]^db[i+1]))) for i in range(len(db)-1)][:12])
    print("  A frame-to-frame dhash deltas:", [int(pc(np.uint64(da[i]^da[i+1]))) for i in range(len(da)-1)][:12])
    # image-space check on the best pair: NMSE of 64x36 gray
    from PIL import Image
    FR=os.path.join(OUT,"frames")
    def crop(fn,t,w=64,h=36):
        im=Image.open(os.path.join(FR,fn,"sec_%04d.jpg"%(int(t*2)+1))).convert("L").resize((w,h))
        return np.asarray(im,dtype=np.float32)
    i,j=np.unravel_index(np.argmin(DH), DH.shape)
    x=crop(sa, A["frames"][i]["t"]); y=crop(sb, B["frames"][j]["t"])
    x=(x-x.mean())/(x.std()+1e-6); y=(y-y.mean())/(y.std()+1e-6)
    print("  pixel-corr of best pair (tA=%.1f,tB=%.1f, dh=%d) = %.3f" % (A["frames"][i]["t"],B["frames"][j]["t"],DH[i,j], float(np.mean(x*y))))
    print("  mean luma %.0f vs %.0f ; 内部帧间 dHash 中位: %.1f vs %.1f" % (
        np.mean([f["luma"] for f in M[sa+".mp4"]]), np.mean([f["luma"] for f in M[sb+".mp4"]]),
        np.median([pc(np.uint64(x)) for x in da[1:] ^ da[:-1]]) if len(da)>1 else 0,
        np.median([pc(np.uint64(x)) for x in db[1:] ^ db[:-1]]) if len(db)>1 else 0))
    print()
for p in (("C1827S03","C1828S03"),("C1897S03","C1898S03"),("C1843S03","C1844S03"),("C1905S03","C1906S03"),("C1840S03","C1841S03")):
    ev(*p)
# also global: how many pairs have pixel-corr > 0.9 at best match?
