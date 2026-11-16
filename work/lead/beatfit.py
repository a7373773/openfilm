
import json, os
WK=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
edl=json.load(open(os.path.join(WK,'edl.json'),encoding='utf-8-sig'))
bar=60.0/102*4   # 2.3529 s
half=bar/2
t=0.0; cuts=[]
for i,s in enumerate(edl['shots']):
    t += float(s['dur']) - float(s.get('trans',0) or 0)
    if i < len(edl['shots'])-1:
        cuts.append(round(t,3))
dev=[abs(((c/bar) % 1.0 + 0.5) % 1.0 - 0.5)*bar for c in cuts]  # distance to nearest bar line
devh=[abs(((c/half) % 1.0 + 0.5) % 1.0 - 0.5)*half for c in cuts]
import numpy as np
print("bar=%.4fs  cuts=%d"%(bar,len(cuts)))
print("dist to BAR line: mean=%.3fs  median=%.3fs  <=0.10s: %d  <=0.15s: %d"%(
    np.mean(dev), np.median(dev), sum(1 for d in dev if d<=0.10), sum(1 for d in dev if d<=0.15)))
print("dist to HALF-bar: mean=%.3fs  <=0.10s: %d"%(np.mean(devh), sum(1 for d in devh if d<=0.10)))
print("expected if random: mean dist to nearest bar = %.3fs"%(bar/4))
