
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
vp=json.load(open(os.path.join(W,'vision','per_clip.json'),encoding='utf-8-sig'))
print(type(vp), len(vp))
if isinstance(vp, dict):
    k=sorted(vp)[0]; print(k, json.dumps(vp[k],ensure_ascii=False)[:800])
else:
    print(json.dumps(vp[0],ensure_ascii=False)[:800])
