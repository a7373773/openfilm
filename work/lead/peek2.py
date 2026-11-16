
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike'
tg=json.load(open(os.path.join(W,'vision','tags.json'),encoding='utf-8-sig'))
print("vision tags: files", len(tg), "recs", sum(len(v) for v in tg.values()))
k=sorted(tg)[0]; print(k, json.dumps(tg[k][:2],ensure_ascii=False))
print()
print("music tree:")
for root,d,f in os.walk(os.path.join(W,'music')):
    for x in f: print(" ", os.path.join(root,x).replace(os.path.join(W,'music'),"."), round(os.path.getsize(os.path.join(root,x))/1e6,2),"MB")
