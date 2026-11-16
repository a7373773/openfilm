# -*- coding: utf-8 -*-
import json, os, math
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
def pct(a,p):
    s=sorted(a); k=(len(s)-1)*p; f=int(math.floor(k)); c=min(f+1,len(s)-1)
    return s[f]+(s[c]-s[f])*(k-f)

allf=[(fn,f) for fn in M for f in M[fn]]
sh=[f["sharp"] for fn,f in allf]; fr=[f["fineratio"] for fn,f in allf]
print("global sharp  p05=%.0f p10=%.0f p20=%.0f p30=%.0f p50=%.0f" % tuple(pct(sh,p) for p in (0.05,0.10,0.20,0.30,0.50)))
print("global fineratio p05=%.3f p10=%.3f p20=%.3f p30=%.3f p50=%.3f" % tuple(pct(fr,p) for p in (0.05,0.10,0.20,0.30,0.50)))

# mask seconds (high+mid, 糊/无细节/遮挡 labels only)
masksec=set()
for fn in S:
    for b in S[fn]["blocked"]:
        if b["conf"] in ("high","mid") and b["label"] in ("BLUR","BLOCK","BLACK","WHITE"):
            for t in range(b["start"], b["end"]+1): masksec.add((fn,t))
print("mask seconds high+mid:", len(masksec))

clean_files=[fn for fn in sorted(S) if S[fn]["usable_ratio"]>=0.98]
cleansec=set((fn,t) for fn in clean_files for t in range(len(M[fn])))

print()
print("X, Y, 剔除全片比例, 剔除clean批比例, mask秒漏过的数量")
for X in (0,150,250,300,400,500,600):
    for Y in (0.00,0.09,0.10,0.11,0.12,0.13):
        if X==0 and Y==0: continue
        rej=sum(1 for fn,f in allf if f["sharp"]<X or f["fineratio"]<Y)
        rejclean=sum(1 for fn in clean_files for f in M[fn] if f["sharp"]<X or f["fineratio"]<Y)
        miss=sum(1 for fn,t in masksec if not (M[fn][t]["sharp"]<X or M[fn][t]["fineratio"]<Y))
        print("  X=%-4d Y=%.2f | 全片剔除 %5.1f%% | clean批剔除 %5.1f%% (%d s) | mask 漏 %d s" % (
            X,Y, 100.0*rej/len(allf), 100.0*rejclean/len(cleansec), 0 if not clean_files else rejclean, miss))
