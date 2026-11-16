
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work'
tags=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
print("tags files:",len(tags),"total recs:",sum(len(v) for v in tags.values()))
print("mask exists:", os.path.exists(os.path.join(W,'analysis','mask.json')))
for f in sorted(tags)[:4]:
    print(" ",f,len(tags[f]),"t range",min(r['t'] for r in tags[f]),max(r['t'] for r in tags[f]))
# nature per file
sf=json.load(open(os.path.join(W,'analysis','scene_feat.json'),encoding='utf-8-sig'))
mf=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
import numpy as np
print()
print("%-16s %6s %6s %6s %6s %6s"%("file","nat","sky","veg","sharp","p_land"))
for f in sorted(mf):
    s=sf.get(f.replace('.mp4',''),[])
    nat=np.mean([r['sky']+r['veg']+r['water'] for r in s]) if s else 0
    sky=np.mean([r['sky'] for r in s]) if s else 0
    veg=np.mean([r['veg'] for r in s]) if s else 0
    sh=np.mean([r['sharp'] for r in mf[f]])
    tg=tags.get(f,[])
    pl=np.mean([r.get('p_landscape',0) for r in tg]) if tg else 0
    print("%-16s %6.3f %6.3f %6.3f %6.0f %6.3f"%(f,nat,sky,veg,sh,pl))
