
import json, os, numpy as np
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
m=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
tg=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
print("%-14s %5s %6s %6s %6s %6s %6s %6s %6s"%("file","nf","luma","sharp","ent","pv","pback","pblur","pblock"))
for f in sorted(m)[-12:]:
    fr=m[f]; tm={round(float(r['t']),1):r for r in tg.get(f,[])}
    def a(k): return np.mean([x[k] for x in fr])
    def b(k): return np.mean([tm.get(round(float(x['t']),1),{}).get(k,0) for x in fr])
    print("%-14s %5d %6.1f %6.0f %6.2f %6.2f %6.2f %6.2f %6.2f"%(
        f,len(fr),a('luma'),a('sharp'),a('entropy'),b('p_wide_vista'),b('p_back'),b('p_blurry'),b('p_blocked')))
print()
print("--- clips with high p_wide_vista (potential summit/vista) ---")
rows=[]
for f in sorted(m):
    tm={round(float(r['t']),1):r for r in tg.get(f,[])}
    pv=np.mean([tm.get(round(float(x['t']),1),{}).get('p_wide_vista',0) for x in m[f]])
    sh=np.mean([x['sharp'] for x in m[f]]); lu=np.mean([x['luma'] for x in m[f]])
    rows.append((f,pv,sh,lu))
for r in sorted(rows,key=lambda x:-x[1])[:10]:
    print("%-14s pv=%.3f sharp=%6.0f luma=%5.1f"%r)
