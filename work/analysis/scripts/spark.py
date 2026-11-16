# -*- coding: utf-8 -*-
import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
RAMP = " .:-=+*#%@"
def spark(vals, ref, width=120):
    out=[]
    for v in vals[:width]:
        r = min(1.0, max(0.0, v/ref if ref>0 else 0))
        out.append(RAMP[min(9, int(r*9.999))])
    return "".join(out)
for fn in sorted(D):
    fr = D[fn]; n=len(fr)
    sh=[f["sharp"] for f in fr]
    ref = sorted(sh)[int(0.95*(n-1))]
    lu=[f["luma"] for f in fr]
    print("%-14s n=%3d sharp(95p=%.0f)" % (fn,n,ref))
    print("  SHARP |%s|" % spark(sh, ref))
    print("  LUMA  |%s|" % spark(lu, 255))
    print()
