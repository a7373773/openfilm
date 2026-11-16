
import json
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision'
pf=json.load(open(P+r'\per_file.json',encoding='utf-8-sig'))
print(json.dumps(pf[0], ensure_ascii=False, indent=1)[:900])
print("---- table ----")
keys=[k for k in pf[0].keys()]
hdr=["file"]+[k for k in keys if k!="file"]
print(" | ".join(hdr))
for r in pf:
    print(" | ".join("%.3f"%r[k] if isinstance(r[k],float) else str(r[k]) for k in hdr))
