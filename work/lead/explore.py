
import json
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
import numpy as np
print("file                 n   luma[p10,p50,p90]        sharp[p10,p50,p90]        uniform[p50,p90]  ent[p10,p50]")
for f in sorted(d):
    fr=d[f]
    lu=np.array([x['luma'] for x in fr]); sh=np.array([x['sharp'] for x in fr])
    un=np.array([x['uniform'] for x in fr]); en=np.array([x['entropy'] for x in fr])
    print("%-20s %3d  %5.0f %5.0f %5.0f    %7.1f %7.1f %8.1f    %.2f %.2f   %.1f %.1f" % (
        f,len(fr),np.percentile(lu,10),np.percentile(lu,50),np.percentile(lu,90),
        np.percentile(sh,10),np.percentile(sh,50),np.percentile(sh,90),
        np.percentile(un,50),np.percentile(un,90),np.percentile(en,10),np.percentile(en,50)))
print()
f='REC-0004-A.mp4'
print("=== detail",f)
for x in d[f]:
    print("t=%3d luma=%6.1f sharp=%8.1f unif=%.2f ent=%.1f dark=%.2f diff=%6.1f sat=%.2f" % (
      x['t'],x['luma'],x['sharp'],x['uniform'],x['entropy'],x['darkfrac'],x['diff'],x['sat']))
