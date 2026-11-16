
import json, os, numpy as np
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
m=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
tg=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
allr=[x for v in m.values() for x in v]
allt=[r for v in tg.values() for r in v]
print("frames metrics",len(allr),"tags",len(allt))
for key in ("p_blocked","p_blurry","p_clear","p_person","p_people","p_wide_vista","p_back","p_landscape","p_landscape_pct"):
    v=np.array([r.get(key,0) for r in allt])
    print("%-16s p10=%.2f p25=%.2f p50=%.2f p75=%.2f p90=%.2f"%(key,*[np.percentile(v,q) for q in (10,25,50,75,90)]))
print()
# per-clip: how many seconds pass a relaxed gate
def tagmap(f): return {round(float(r['t']),1):r for r in tg.get(f,[])}
rows=[]
for f in sorted(m):
    fr=m[f]; tm=tagmap(f)
    sh=np.array([x['sharp'] for x in fr]); med=float(np.median(sh)); floor=max(120,0.30*med)
    okc=0; reasons={'soft':0,'flat':0,'expo':0,'blocked':0,'blurry':0}
    for x in fr:
        t=round(float(x['t']),1); tr=tm.get(t,{})
        if x['sharp']<floor: reasons['soft']+=1; continue
        if x['entropy']<4.3: reasons['flat']+=1; continue
        if x['luma']<45 or x['luma']>214: reasons['expo']+=1; continue
        if tr.get('p_blocked',0)>0.55: reasons['blocked']+=1; continue
        if tr.get('p_blurry',0)>0.65: reasons['blurry']+=1; continue
        okc+=1
    rows.append((f,len(fr),okc,reasons,med))
tot_pass=sum(r[2] for r in rows)
print("total passing frames:",tot_pass,"of",sum(r[1] for r in rows))
import collections
c=collections.Counter()
for r in rows:
    for k,v in r[3].items(): c[k]+=v
print("reject reasons:",dict(c))
print()
print("%-14s %4s %4s  %s"%("file","nf","ok","reasons"))
for r in rows:
    if r[2]==0: print("%-14s %4d %4d  %s"%(r[0],r[1],r[2],{k:v for k,v in r[3].items() if v}))
