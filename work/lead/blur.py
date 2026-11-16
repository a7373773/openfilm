
import json, numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
def runs(idx):
    out=[];s=None;prev=None
    for i in idx:
        if s is None: s=i
        elif i!=prev+1: out.append((s,prev)); s=i
        prev=i
    if s is not None: out.append((s,prev))
    return out
print("%-16s %6s %8s %s"%("file","med","p10sharp","blur runs (sharp < 0.35*median or <55)"))
for f in sorted(d):
    sh=np.array([x["sharp"] for x in d[f]])
    med=float(np.median(sh))
    thr=max(55.0, 0.35*med)
    idx=[i for i,v in enumerate(sh) if v<thr]
    r=runs(idx)
    r=[(a,b) for a,b in r if b-a+1>=1]
    print("%-16s %6.0f %8.0f  thr=%5.0f  n=%3d  %s"%(f,med,np.percentile(sh,10),thr,len(idx),r if len(r)<=12 else r[:12]+["..."]))
