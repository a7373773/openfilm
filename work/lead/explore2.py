
import json
import numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))

def runs(flags, t0=0):
    out=[]; s=None
    for i,f in enumerate(flags):
        if f and s is None: s=i
        if not f and s is not None:
            out.append((s+t0, i-1+t0)); s=None
    if s is not None: out.append((s+t0,len(flags)-1+t0))
    return out

print("=== per-file blocked-ish seconds ===")
for f in sorted(d):
    fr=d[f]
    lu=np.array([x['luma'] for x in fr]); sh=np.array([x['sharp'] for x in fr])
    un=np.array([x['uniform'] for x in fr]); en=np.array([x['entropy'] for x in fr])
    dk=np.array([x['darkfrac'] for x in fr])
    # blocked heuristics
    b = (un>0.55) | (sh<45) | (lu<55) | (lu>232) | (dk>0.75) | (en<3.0)
    r = runs(b.tolist())
    tot=int(b.sum())
    print("%-20s blocked=%3d/%3d  runs=%s" % (f, tot, len(fr), r if len(r)<=8 else r[:8]+['...']))

print()
print("=== histograms of low-sharp / high-uniform across all ===")
allsh=[]; allun=[]; alllu=[]
for f in d:
    for x in d[f]:
        allsh.append(x['sharp']); allun.append(x['uniform']); alllu.append(x['luma'])
allsh=np.array(allsh); allun=np.array(allun); alllu=np.array(alllu)
print("sharp pct:", [round(float(np.percentile(allsh,p)),1) for p in [1,5,10,25,50,75,90,99]])
print("uniform pct:", [round(float(np.percentile(allun,p)),3) for p in [1,5,10,25,50,75,90,99]])
print("luma pct:", [round(float(np.percentile(alllu,p)),1) for p in [1,5,10,25,50,75,90,99]])
