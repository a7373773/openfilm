
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis'
d=json.load(open(os.path.join(W,'per_clip.json'),encoding='utf-8-sig'))
print(type(d), len(d))
k = d[0] if isinstance(d,list) else list(d.keys())[0]
print(json.dumps(k, ensure_ascii=False, indent=1)[:1200] if isinstance(d,list) else "keys:"+str(list(d[k].keys())))
if isinstance(d,list):
    print("\n--- 3 rows ---")
    for r in d[:3]: print(json.dumps(r,ensure_ascii=False)[:400])
