# -*- coding: utf-8 -*-
import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
mask = json.load(open(os.path.join(OUT,"mask.json"), encoding="utf-8"))
mask2 = json.load(open(os.path.join(OUT,"mask.json"), encoding="utf-8"))
assert mask == mask2, "mask json roundtrip mismatch"
tot = sum(len(M[fn]) for fn in M)
clean=[fn for fn in sorted(S) if S[fn]["usable_ratio"]>=0.98]
def mm(t):
    t=int(round(t)); return "%d:%02d"%(t//60,t%60)
def union(X=None):
    s=set()
    for fn in mask:
        for a,b,sev,sh,fr in mask[fn]["runs"]:
            for t in range(a,b): s.add((fn,t))
    if X is not None:
        for fn in M:
            for f in M[fn]:
                if f["sharp"] < X: s.add((fn,f["t"]))
    return s
u250=union(250); u300=union(300)
print("X=250 union: %d s (%.1f%%) clean loss %d" % (len(u250), 100.0*len(u250)/tot, sum(1 for fn in clean for t in range(len(M[fn])) if (fn,t) in u250)))
print("X=300 union: %d s (%.1f%%) clean loss %d" % (len(u300), 100.0*len(u300)/tot, sum(1 for fn in clean for t in range(len(M[fn])) if (fn,t) in u300)))
print()
print("FLATS intervals (excluded from mask on purpose):")
fl=[]
for fn in sorted(S):
    for b in S[fn]["blocked"]:
        if b["label"] == "FLATS":
            fl.append((fn,b))
            print("  %-16s %s-%s %2ds conf=%s uni=%.2f lumastd=%.1f sharp=%.0f fr=%.3f" % (
                fn, mm(b["start"]), mm(b["end"]+1), b["dur"], b["conf"], b["median_uniform"], b["median_lumastd"], b["median_sharp"], b["median_fineratio"]))
print("count:", len(fl))
print()
print("mask high+mid only (no mid-lowtex) seconds:", sum(b-a for fn in mask for a,b,sev,sh,fr in mask[fn]["runs"] if sev!="mid-lowtex"))
print("mid-lowtex runs:")
for fn in sorted(mask):
    for a,b,sev,sh,fr in mask[fn]["runs"]:
        if sev=="mid-lowtex": print("  %-16s %s-%s %ds sharp=%.0f fr=%.3f" % (fn, mm(a), mm(b), b-a, sh, fr))
