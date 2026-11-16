import json, os, math, statistics as st
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
def pct(a,p):
    s=sorted(a); k=(len(s)-1)*p; f=int(math.floor(k)); c=min(f+1,len(s)-1)
    return s[f]+(s[c]-s[f])*(k-f)
print("%-16s %5s | %-28s | %-22s" % ("file","n","fineratio p05/25/50/75/95","sharp p05/50/95"))
for fn in sorted(D):
    fr=D[fn]
    fr_=[f["fineratio"] for f in fr]; sh=[f["sharp"] for f in fr]
    print("%-16s %5d | %s | %s" % (fn,len(fr),
        "/".join("%.2f"%pct(fr_,p) for p in (0.05,0.25,0.5,0.75,0.95)),
        "/".join("%.0f"%pct(sh,p) for p in (0.05,0.5,0.95))))
allf=[f["fineratio"] for fn in D for f in D[fn]]
print()
print("global fineratio percentiles:", ["p%02d=%.3f"%(p*100,pct(allf,p)) for p in (0.05,0.1,0.2,0.5,0.8,0.9,0.95)])
