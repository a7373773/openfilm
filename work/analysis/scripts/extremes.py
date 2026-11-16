# -*- coding: utf-8 -*-
import json, os, math
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
rows=[]
for fn in D:
    for f in D[fn]:
        rows.append((fn, f))
print("=== 30 frames with LOWEST sharp ===")
for fn,f in sorted(rows, key=lambda r: r[1]["sharp"])[:30]:
    print("%-14s t=%3d sharp=%7.1f grad=%6.1f edge=%.3f luma=%5.1f std=%5.1f dark=%.2f bri=%.2f colf=%5.1f sat=%.2f uni=%.2f flat=%.2f ent=%.2f warm=%.2f diff=%5.1f" % (
        fn, f["t"], f["sharp"], f["grad"], f["edgefrac"], f["luma"], f["lumastd"], f["darkfrac"], f["brightfrac"],
        f["colorful"], f["sat"], f["uniform"], f["flatfrac"], f["entropy"], f["warmfrac"], f["diff"]))
print()
print("=== 25 frames with LOWEST edgefrac ===")
for fn,f in sorted(rows, key=lambda r: r[1]["edgefrac"])[:25]:
    print("%-14s t=%3d edge=%.3f sharp=%7.1f luma=%5.1f uni=%.2f flat=%.2f ent=%.2f warm=%.2f colf=%5.1f" % (
        fn, f["t"], f["edgefrac"], f["sharp"], f["luma"], f["uniform"], f["flatfrac"], f["entropy"], f["warmfrac"], f["colorful"]))
print()
print("=== 20 frames with HIGHEST uniform ===")
for fn,f in sorted(rows, key=lambda r: -r[1]["uniform"])[:20]:
    print("%-14s t=%3d uni=%.2f flat=%.2f ent=%.2f sharp=%7.1f luma=%5.1f std=%5.1f colf=%5.1f" % (
        fn, f["t"], f["uniform"], f["flatfrac"], f["entropy"], f["sharp"], f["luma"], f["lumastd"], f["colorful"]))
print()
print("=== 20 frames with HIGHEST warmfrac ===")
for fn,f in sorted(rows, key=lambda r: -r[1]["warmfrac"])[:20]:
    print("%-14s t=%3d warm=%.2f sharp=%7.1f luma=%5.1f std=%5.1f ent=%.2f colf=%5.1f sat=%.2f edge=%.3f" % (
        fn, f["t"], f["warmfrac"], f["sharp"], f["luma"], f["lumastd"], f["entropy"], f["colorful"], f["sat"], f["edgefrac"]))
print()
print("=== 15 frames with lowest luma / highest darkfrac ===")
for fn,f in sorted(rows, key=lambda r: r[1]["luma"])[:15]:
    print("%-14s t=%3d luma=%5.1f dark=%.2f std=%5.1f sharp=%7.1f ent=%.2f uni=%.2f colf=%5.1f" % (
        fn, f["t"], f["luma"], f["darkfrac"], f["lumastd"], f["sharp"], f["entropy"], f["uniform"], f["colorful"]))
