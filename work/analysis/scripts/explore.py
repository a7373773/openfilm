# -*- coding: utf-8 -*-
import json, os, math, statistics as st
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
PS = (0.05,0.25,0.5,0.75,0.9,0.95)
def q(a,p):
    s=sorted(a); k=(len(s)-1)*p; f=int(math.floor(k)); c=min(f+1,len(s)-1)
    return s[f]+(s[c]-s[f])*(k-f)
print("%-16s %5s | %-32s | %-26s | %-22s | %-22s" % ("file","n","sharp p05/25/50/75/90/95","grad p50/90/95","luma p05/50/95","colorful p05/50/95"))
for fn in sorted(D):
    fr=D[fn]; n=len(fr)
    sh=[f["sharp"] for f in fr]; gr=[f["grad"] for f in fr]; lu=[f["luma"] for f in fr]
    co=[f["colorful"] for f in fr]; wf=[f["warmfrac"] for f in fr]; df=[f["darkfrac"] for f in fr]
    ef=[f["edgefrac"] for f in fr]; un=[f["uniform"] for f in fr]; en=[f["entropy"] for f in fr]
    print("%-16s %5d | %s | %s | %s | %s | edge p50 %.3f uni p50 %.2f ent p50 %.2f warm p50 %.2f darkmax %.2f" % (
        fn, n,
        "/".join("%d"%q(sh,p) for p in PS),
        "%d/%d/%d"%(q(gr,.5),q(gr,.9),q(gr,.95)),
        "%.0f/%.0f/%.0f"%(q(lu,.05),q(lu,.5),q(lu,.95)),
        "%.0f/%.0f/%.0f"%(q(co,.05),q(co,.5),q(co,.95)),
        q(ef,.5), q(un,.5), q(en,.5), q(wf,.5), max(df)))
print()
print("=== GLOBAL sharp distribution over all frames ===")
allsh=[f["sharp"] for fn in D for f in D[fn]]
allgr=[f["grad"] for fn in D for f in D[fn]]
allef=[f["edgefrac"] for fn in D for f in D[fn]]
for p in (0.01,0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.95,0.99):
    print("  p%02d sharp=%7.1f grad=%6.1f edgefrac=%.4f" % (p*100, q(allsh,p), q(allgr,p), q(allef,p)))
print("total frames", len(allsh))
