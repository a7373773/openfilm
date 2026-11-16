# -*- coding: utf-8 -*-
import json, os, math
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
mask = json.load(open(os.path.join(OUT,"mask.json"), encoding="utf-8"))
tot = sum(len(M[fn]) for fn in M)
def union_sec(X=None, Y=None, include_midlowtex=True):
    s=set()
    for fn in mask:
        for a,b,sev,sh,fr in mask[fn]["runs"]:
            if sev == "mid-lowtex" and not include_midlowtex: continue
            for t in range(a,b): s.add((fn,t))
    if X is not None:
        for fn in M:
            for f in M[fn]:
                if f["sharp"] < X or (Y is not None and f["fineratio"] < Y): s.add((fn,f["t"]))
    return s
mask_only = union_sec()
with_ml = union_sec()
clean=[fn for fn in sorted(S) if S[fn]["usable_ratio"]>=0.98]
print("total seconds:", tot)
print("A) mask only (all 3 sev):            %4d s = %5.1f%%" % (len(mask_only), 100.0*len(mask_only)/tot))
def cl(s): return sum(1 for fn in clean for t in range(len(M[fn])) if (fn,t) in s)
print("B) mask + sharp>=300:                 %4d s = %5.1f%%  | clean批损失 %2d s" % (len(union_sec(300)), 100.0*len(union_sec(300))/tot, cl(union_sec(300))))
print("C) mask + sharp>=300 + fr>=0.09:      %4d s = %5.1f%%  | clean批损失 %2d s" % (len(union_sec(300,0.09)), 100.0*len(union_sec(300,0.09))/tot, cl(union_sec(300,0.09))))
print("D) mask + sharp>=400:                 %4d s = %5.1f%%  | clean批损失 %2d s" % (len(union_sec(400)), 100.0*len(union_sec(400))/tot, cl(union_sec(400))))
print("E) mask(排除 mid-lowtex) 仅 high+mid:  %4d s = %5.1f%%" % (len(union_sec(include_midlowtex=False)), 100.0*len(union_sec(include_midlowtex=False))/tot))
print()
print("clean files:", len(clean), "clean seconds:", sum(len(M[fn]) for fn in clean))
for fn in sorted(mask):
    if not mask[fn]["runs"]: print("  %-16s runs=[] dur=%d" % (fn, mask[fn]["dur"]))
