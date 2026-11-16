
import json, numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
allrows=[(f,x) for f in d for x in d[f]]
print("=== extremes ===")
print("-- lowest entropy --")
for f,x in sorted(allrows,key=lambda r:r[1]["entropy"])[:12]:
    print("%-16s t=%3d ent=%.2f unif=%.2f sharp=%7.1f luma=%5.1f dark=%.2f diff=%5.1f"%(f,x["t"],x["entropy"],x["uniform"],x["sharp"],x["luma"],x["darkfrac"],x["diff"]))
print("-- highest uniform --")
for f,x in sorted(allrows,key=lambda r:-r[1]["uniform"])[:12]:
    print("%-16s t=%3d ent=%.2f unif=%.2f sharp=%7.1f luma=%5.1f dark=%.2f diff=%5.1f"%(f,x["t"],x["entropy"],x["uniform"],x["sharp"],x["luma"],x["darkfrac"],x["diff"]))
print("-- lowest diff (static) --")
for f,x in sorted(allrows,key=lambda r:r[1]["diff"])[:15]:
    print("%-16s t=%3d ent=%.2f unif=%.2f sharp=%7.1f luma=%5.1f diff=%5.2f"%(f,x["t"],x["entropy"],x["uniform"],x["sharp"],x["luma"],x["diff"]))
print("-- low sharp --")
for f,x in sorted(allrows,key=lambda r:r[1]["sharp"])[:12]:
    print("%-16s t=%3d ent=%.2f unif=%.2f sharp=%7.1f luma=%5.1f"%(f,x["t"],x["entropy"],x["uniform"],x["sharp"],x["luma"]))
print()
print("=== seconds with diff<1.5 (static) ===")
for f in sorted(d):
    st=[x["t"] for x in d[f] if x["diff"]<1.5]
    if st: print("%-16s %d secs %s"%(f,len(st),st[:30]))
