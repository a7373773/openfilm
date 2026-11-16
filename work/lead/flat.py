
import json, numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
rows=[(f,x) for f in d for x in d[f]]
ff=np.array([x["flatfrac"] for f,x in rows])
print("flatfrac percentiles:", {p: round(float(np.percentile(ff,p)),3) for p in [50,75,90,95,99,99.5,100]})
print()
print("-- top flatfrac seconds --")
for f,x in sorted(rows,key=lambda r:-r[1]["flatfrac"])[:20]:
    print("%-16s t=%3d flat=%.2f sharp=%7.1f luma=%5.1f ent=%.2f unif=%.2f"%(f,x["t"],x["flatfrac"],x["sharp"],x["luma"],x["entropy"],x["uniform"]))
print()
print("-- per file: seconds with flatfrac>=0.9 / >=0.75 counts and runs --")
def runs(idx):
    out=[];s=None;prev=None
    for i in idx:
        if s is None: s=i
        elif i!=prev+1: out.append((s,prev)); s=i
        prev=i
    if s is not None: out.append((s,prev))
    return out
for f in sorted(d):
    fr=d[f]
    i90=[i for i,x in enumerate(fr) if x["flatfrac"]>=0.9]
    i75=[i for i,x in enumerate(fr) if x["flatfrac"]>=0.75]
    print("%-16s n90=%3d %-40s n75=%3d %s"%(f,len(i90),str(runs(i90))[:40],len(i75),str(runs(i75))[:60]))
