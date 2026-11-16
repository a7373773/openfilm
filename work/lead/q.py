
import json, numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
for f,a,b in [("REC-0008-A.mp4",86,98),("REC-0007-A.mp4",1,12),("REC-0007-A.mp4",28,38)]:
    print("==",f)
    for x in d[f]:
        if a<=x["t"]<=b:
            print("  t=%3d sharp=%7.1f luma=%5.1f ent=%.2f unif=%.2f diff=%5.1f"%(x["t"],x["sharp"],x["luma"],x["entropy"],x["uniform"],x["diff"]))
