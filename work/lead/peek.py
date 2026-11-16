
import json
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision\sample_tags.json'
d=json.load(open(P,encoding='utf-8-sig'))
print(type(d), (list(d.keys())[:5] if isinstance(d,dict) else len(d)))
if isinstance(d,dict):
    k=list(d.keys())[0]; print(k, json.dumps(d[k], ensure_ascii=False)[:600])
elif isinstance(d,list):
    print(json.dumps(d[:3], ensure_ascii=False, indent=1)[:1200])
