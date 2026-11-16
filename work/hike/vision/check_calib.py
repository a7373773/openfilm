
# -*- coding: utf-8 -*-
import json, os, math, statistics as st, collections
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
aux  = json.load(open(os.path.join(V,"aux.json"), encoding="utf-8"))
pix  = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))

rows=[]
for clip, rr in tags.items():
    c = clip.replace(".mp4","")
    ax = {r["seq"]: r for r in aux.get(c, [])}
    for r in rr:
        seq = int(round(r["t"]/0.5))+1
        p = pix.get(c,{}).get(str(seq)); a = ax.get(seq)
        if p and a: rows.append((c, seq, r, a, p))
print("frames", len(rows))

def q(v, x):
    v=sorted(v); k=(len(v)-1)*x; lo=int(k); hi=min(lo+1,len(v)-1); return v[lo]+(v[hi]-v[lo])*(k-lo)
def show(name, vals):
    print("  %-14s min %.4f  p10 %.4f  p50 %.4f  p90 %.4f  max %.4f  mean %.4f" % (name, min(vals), q(vals,.1), q(vals,.5), q(vals,.9), max(vals), sum(vals)/len(vals)))
print("\n== objective distribution ==")
for k in ["lapvar","edge","skyfrac","greenfrac","flatfrac","topLap","botLap","topMean","botMean","vertGrad","colorful","mean"]:
    show(k, [r[4][k] for r in rows])

# geometry-based "pointing down" heuristic: low sky AND top half has as much texture as bottom half
def down_score(p):
    ratio = p["topLap"]/max(1e-6, p["botLap"])
    return (1.0 if p["skyfrac"] < 0.10 else 0.0) + (0.5 if 0.5 <= ratio <= 2.0 else 0.0) + (0.5 if abs(p["vertGrad"]) < 0.06 else 0.0)
print("\n== crosstab: CLIP p_closeup vs geometry 'pointing down' ==")
buckets = collections.defaultdict(list)
for c,seq,r,a,p in rows:
    b = "closeup>=0.7" if r["p_closeup"]>=0.7 else ("closeup<=0.2" if r["p_closeup"]<=0.2 else "mid")
    buckets[b].append(p)
for b in ["closeup>=0.7","mid","closeup<=0.2"]:
    v=buckets[b]
    if not v: continue
    print("  %-12s n=%3d  skyfrac %.2f  topLap %.4f  botLap %.4f  topMean %.2f botMean %.2f  lapvar %.4f" % (
        b, len(v), sum(x["skyfrac"] for x in v)/len(v), sum(x["topLap"] for x in v)/len(v),
        sum(x["botLap"] for x in v)/len(v), sum(x["topMean"] for x in v)/len(v), sum(x["botMean"] for x in v)/len(v),
        sum(x["lapvar"] for x in v)/len(v)))

print("\n== crosstab: CLIP p_person vs objective ==")
b2 = collections.defaultdict(list)
for c,seq,r,a,p in rows:
    b = "person>=0.9" if r["p_person"]>=0.9 else ("person 0.5-0.9" if r["p_person"]>=0.5 else "person<0.5")
    b2[b].append((p,a,r))
for b in ["person>=0.9","person 0.5-0.9","person<0.5"]:
    v=b2[b]
    if not v: continue
    print("  %-14s n=%3d skin %.3f edge %.3f lapvar %.4f green %.2f sky %.2f | aux p_human %.2f" % (
        b, len(v), sum(x[0]["skin"] for x in v)/len(v), sum(x[0]["edge"] for x in v)/len(v),
        sum(x[0]["lapvar"] for x in v)/len(v), sum(x[0]["greenfrac"] for x in v)/len(v),
        sum(x[0]["skyfrac"] for x in v)/len(v), sum(x[1]["p_human"] for x in v)/len(v)))

print("\n== how many frames are 'pointing at ground' by strict objective rule ==")
strict = [(c,seq,r) for c,seq,r,a,p in rows if p["skyfrac"]<0.05 and p["topLap"]>0.015 and abs(p["vertGrad"])<0.08]
print("  strict ground-like frames: %d / %d (%.1f%%)" % (len(strict), len(rows), 100*len(strict)/len(rows)))
print("  of those, mean CLIP p_closeup = %.2f ; mean p_person = %.2f" % (
    sum(r["p_closeup"] for _,_,r in strict)/max(1,len(strict)), sum(r["p_person"] for _,_,r in strict)/max(1,len(strict))))
cl = collections.Counter(c for c,_,_ in strict)
print("  clips most affected:", dict(cl.most_common(8)))

print("\n== p_blurry sanity: mean lapvar by p_blurry bucket ==")
b3 = collections.defaultdict(list)
for c,seq,r,a,p in rows:
    k = "blurry>=0.7" if r["p_blurry"]>=0.7 else ("blurry 0.4-0.7" if r["p_blurry"]>=0.4 else "blurry<0.4")
    b3[k].append((p,r))
for k in ["blurry>=0.7","blurry 0.4-0.7","blurry<0.4"]:
    v=b3[k]
    if not v: continue
    print("  %-14s n=%3d lapvar %.4f edge %.3f  p_clear %.2f" % (k, len(v),
        sum(x[0]["lapvar"] for x in v)/len(v), sum(x[0]["edge"] for x in v)/len(v), sum(x[1]["p_clear"] for x in v)/len(v)))
