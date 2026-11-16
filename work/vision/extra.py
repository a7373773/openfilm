
import json, os, collections, statistics as st
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
pf = json.load(open(os.path.join(V,"per_file.json"), encoding="utf-8"))
sm = json.load(open(os.path.join(V,"summary.json"), encoding="utf-8"))

# what blocks: among seconds with p_blocked>0.5, which component dominates
dom = collections.Counter()
for f, rows in tags.items():
    for r in rows:
        if r["p_blocked"] > 0.5:
            comp = max([("hand", r["p_hand"]), ("fabric", r["p_fabric"]), ("closeup", r["p_closeup"])], key=lambda x: x[1])
            dom[comp[0]] += 1
print("blocked seconds by dominant component:", dict(dom), "total", sum(dom.values()))

# blocked seconds and ratio per file
blocked_by_file = {}
for s in sm["blocked_segments"]:
    blocked_by_file[s["file"]] = blocked_by_file.get(s["file"], 0) + s["dur"]
print("\ntop 8 files by blocked seconds:")
for f, v in sorted(blocked_by_file.items(), key=lambda x: -x[1])[:8]:
    n = len(tags[f]); print("  %-14s %3ds / %3ds (%.0f%%)" % (f.replace('.mp4',''), v, n, 100*v/n))

# files with NO blocked segments / no candidate
cand_by_file = collections.Counter(c["file"] for c in json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8")))
print("\nfiles with zero candidates:")
for r in pf:
    if cand_by_file.get(r["file"], 0) == 0:
        print("  %-14s ratio=%.2f meanL=%.3f meanBlk=%.3f" % (r["file"].replace(".mp4",""), r["landscape_ratio"], r["mean_p_landscape"], r["mean_p_blocked"]))

# correlation p_blocked with objective stats over ALL frames
import math
def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a)); sb=math.sqrt(sum((x-mb)**2 for x in b))
    return 0 if sa==0 or sb==0 else sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)
rows=[]
for f, rr in tags.items():
    d=f.replace(".mp4","")
    for r in rr:
        p=pix.get(d,{}).get(str(r["t"]))
        if p: rows.append((r,p))
print("\ncorrelation over %d frames:" % len(rows))
for k in ["skin","lapvar","edge","flatfrac","skyfrac","mean","dark","colorful"]:
    print("  p_blocked vs %-9s %+.3f | p_landscape vs %-9s %+.3f" % (
        k, corr([r["p_blocked"] for r,_ in rows],[p[k] for _,p in rows]),
        k, corr([r["p_landscape"] for r,_ in rows],[p[k] for _,p in rows])))

# landscape ratio for sky-heavy frames - is there sky? check mean skyfrac of top/bottom quartile by p_landscape
rows.sort(key=lambda x: x[0]["p_landscape"])
q=len(rows)//4
print("\nmean objective stats by p_landscape quartile:")
for name, part in [("Q1 lowest", rows[:q]), ("Q2", rows[q:2*q]), ("Q3", rows[2*q:3*q]), ("Q4 highest", rows[3*q:])]:
    print("  %-10s lapvar=%.4f edge=%.3f flat=%.2f sky=%.2f colorful=%.3f mean=%.2f skin=%.3f" % (
        name, sum(p["lapvar"] for _,p in part)/len(part), sum(p["edge"] for _,p in part)/len(part),
        sum(p["flatfrac"] for _,p in part)/len(part), sum(p["skyfrac"] for _,p in part)/len(part),
        sum(p["colorful"] for _,p in part)/len(part), sum(p["mean"] for _,p in part)/len(part),
        sum(p["skin"] for _,p in part)/len(part)))

# per-file sorted list for message
print("\nall files (landscape_ratio, meanBlk, medL):")
for r in sorted(pf, key=lambda r: r["landscape_ratio"]):
    print("  %-14s ratio=%.2f meanL=%.3f medL=%.3f blk=%.3f blur=%.3f n=%d" % (
        r["file"].replace(".mp4",""), r["landscape_ratio"], r["mean_p_landscape"], r["median_p_landscape"], r["mean_p_blocked"], r["mean_p_blurry"], r["frames"]))
print("\ncandidates per file:", dict(cand_by_file))
print("total cand secs", sm["candidate_secs"], "blocked secs", sm["blocked_secs"])
