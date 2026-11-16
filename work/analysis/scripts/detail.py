# -*- coding: utf-8 -*-
import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
def show(fn, t0, t1):
    fr = D[fn]
    print("=== %s  t=%d..%d ===" % (fn,t0,t1))
    for f in fr:
        if t0 <= f["t"] <= t1:
            print(" t=%3d sharp=%7.1f grad=%6.1f edge=%.3f luma=%5.1f std=%5.1f dark=%.2f bri=%.2f colf=%5.1f sat=%.2f uni=%.2f flat=%.2f ent=%.2f warm=%.2f diff=%5.1f" % (
              f["t"], f["sharp"], f["grad"], f["edgefrac"], f["luma"], f["lumastd"], f["darkfrac"], f["brightfrac"],
              f["colorful"], f["sat"], f["uniform"], f["flatfrac"], f["entropy"], f["warmfrac"], f["diff"]))
    print()
show("REC-0007-A.mp4", 0, 40)
show("REC-0005-A.mp4", 0, 24)
show("REC-0006-A.mp4", 70, 100)
