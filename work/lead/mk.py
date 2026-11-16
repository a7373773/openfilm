
import json, os
W=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work'
mk=json.load(open(os.path.join(W,'analysis','mask.json'),encoding='utf-8-sig'))
print("type",type(mk),"n",len(mk))
k=list(mk.keys())[0]
print("sample", k, json.dumps(mk[k], ensure_ascii=False)[:400])
print()
tot=0
for f in sorted(mk):
    ent=mk[f]; runs=ent.get("runs") if isinstance(ent,dict) else ent
    n=sum(int(r[1])-int(r[0]) for r in (runs or []))
    tot+=n
    print("%-16s masked=%3ds runs=%s"%(f,n,str(runs)[:90]))
print("total masked sec:",tot)
