
import json, os
import numpy as np
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work'
edl=json.load(open(os.path.join(W,'lead','edl.json'),encoding='utf-8-sig'))
mf=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
sf=json.load(open(os.path.join(W,'analysis','scene_feat.json'),encoding='utf-8-sig'))
tg=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
print("%2s %-16s %6s %6s %6s %6s %6s %6s %6s %6s"%("#","file","t","sky","flat","ent","sharp","colorful","pl","skyfrac_det"))
bad=[]
for i,s in enumerate(edl['shots']):
    f=s['file']; a=int(s['start']); b=int(round(s['start']+s['dur']*s['speed']))
    idx=[x for x in range(a,b+1) if x < len(mf[f])]
    m=[mf[f][j] for j in idx]
    nat=[x for x in sf.get(f.replace('.mp4',''),[]) if a<=x['t']<=b]
    tgs=[x for x in tg.get(f,[]) if a<=int(x['t'])-1<=b]
    sky=np.mean([x['sky'] for x in nat]) if nat else 0
    skyf=np.mean([x['flatfrac'] for x in m])
    ent=np.mean([x['entropy'] for x in m]); sh=np.mean([x['sharp'] for x in m])
    cf=np.mean([x['colorful'] for x in m])
    pl=np.mean([x['p_landscape'] for x in tgs]) if tgs else 0
    flag=""
    if (sky>0.80 and ent<5.0) or skyf>0.2 or ent<4.7: flag="SUSPECT-BLANK"; bad.append(i)
    print("%2d %-16s %6d %6.2f %6.2f %6.2f %6.0f %6.1f %6.2f  %s"%(i,f,a,sky,skyf,ent,sh,cf,pl,flag))
print("\nsuspect shots:",bad)
