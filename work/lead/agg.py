
import json, numpy as np
P=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\metrics.json'
d=json.load(open(P,encoding='utf-8-sig'))
print("%-18s %6s %6s %6s %6s %6s %6s %6s"%("file","n","luma","sharp","unif","ent","colorful","diff"))
rows=[]
for f in sorted(d):
    fr=d[f]
    g=lambda k: np.array([x[k] for x in fr])
    m={k: float(np.mean(g(k))) for k in ("luma","sharp","uniform","entropy","colorful","diff")}
    rows.append((f,len(fr),m))
    print("%-18s %6d %6.1f %6.0f %6.3f %6.2f %6.1f %6.1f"%(f,len(fr),m["luma"],m["sharp"],m["uniform"],m["entropy"],m["colorful"],m["diff"]))
# outliers
import statistics
for k in ("sharp","uniform","entropy","colorful","luma"):
    vals=[r[2][k] for r in rows]
    mu,sd=statistics.mean(vals),statistics.pstdev(vals)
    out=[(r[0],round(r[2][k],2)) for r in rows if abs(r[2][k]-mu)>2*sd]
    print("%-10s mean=%.2f sd=%.2f  outliers=%s"%(k,mu,sd,out))
