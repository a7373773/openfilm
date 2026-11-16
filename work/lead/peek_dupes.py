
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis'
for f in ("dupes_raw.json","dupes_related.json"):
    p=os.path.join(W,f)
    if not os.path.exists(p): print(f,"missing"); continue
    d=json.load(open(p,encoding='utf-8-sig'))
    print("==",f,type(d), len(d) if hasattr(d,'__len__') else '')
    s=json.dumps(d,ensure_ascii=False)[:1500]
    print(s)
    print()
