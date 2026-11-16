
import json, os
from collections import Counter
p=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\edl.json'
d=json.load(open(p,encoding='utf-8-sig'))
c=Counter((s.get('trans_type') or 'cut') for s in d['shots'])
print(dict(c))
print("shots", len(d['shots']), "overlays", len(d.get('overlays',[])))
