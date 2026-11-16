
import json, os
import numpy as np
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work'
mf=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
mk=json.load(open(os.path.join(W,'analysis','mask.json'),encoding='utf-8-sig'))
tg=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
sf=json.load(open(os.path.join(W,'analysis','scene_feat.json'),encoding='utf-8-sig'))
def masked(f):
    s=set()
    ent=mk.get(f) or {}
    for r in (ent.get('runs') or []):
        for t in range(int(r[0]),int(r[1])): s.add(t)
    return s
print("%-16s %5s %5s %6s %6s %6s %6s %6s"%("file","sec","masked","sharpOK","clipOK","both","plmean","closeup"))
rows=[]
for f in sorted(mf):
    ms=masked(f)
    tagmap={}
    for r in tg.get(f,[]):
        tagmap.setdefault(int(r['t'])-1,r)
    nat={int(x['t']):x for x in sf.get(f.replace('.mp4',''),[])}
    n=len(mf[f]); sh=[x['sharp'] for x in mf[f]]
    ok_sharp=sum(1 for i in range(n) if i not in ms and sh[i]>=300)
    ok_clip=0; both=0
    for i in range(n):
        tr=tagmap.get(i,{})
        pl=tr.get('p_landscape'); pb=tr.get('p_blocked'); pp=tr.get('p_landscape_pct')
        c = (pl is not None and pl>=0.35 and (pb is None or pb<=0.45) and (pp is None or pp>=0.55))
        if c: ok_clip+=1
        if c and i not in ms and sh[i]>=300: both+=1
    plm=np.mean([t.get('p_landscape',0) for t in tg.get(f,[])]) if tg.get(f) else 0
    cu=np.mean([t.get('p_closeup',0) for t in tg.get(f,[])]) if tg.get(f) else 0
    print("%-16s %5d %5d %6d %6d %6d %6.3f %6.3f"%(f,n,len(ms),ok_sharp,ok_clip,both,plm,cu))
    rows.append((f,both))
print("\ntotal both:",sum(r[1] for r in rows))
print("files with both>=8:",[r[0] for r in sorted(rows,key=lambda x:-x[1]) if r[1]>=8])
