
import json, os, numpy as np
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
m=json.load(open(os.path.join(W,'analysis','metrics.json'),encoding='utf-8-sig'))
print("files",len(m))
k=sorted(m)[0]
print(k,"frames",len(m[k]))
print(json.dumps(m[k][:2],ensure_ascii=False))
print()
# global distributions
allr=[x for v in m.values() for x in v]
for key in ("sharp","lapvar","fineratio","edgefrac","entropy","luma","sat","colorful","diff","flatfrac","sky","green"):
    if key in allr[0]:
        v=np.array([x[key] for x in allr])
        print("%-10s p5=%8.2f p50=%8.2f p95=%8.2f"%(key,np.percentile(v,5),np.percentile(v,50),np.percentile(v,95)))
print()
print("keys:", list(allr[0].keys()))
