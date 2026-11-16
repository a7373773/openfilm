
import json, math, os
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = []
with open(os.path.join(V, "sample_tags.json.ndjson"), encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if line: tags.append(json.loads(line))
pix = json.load(open(os.path.join(V, "pixstats.json"), encoding="utf-8"))
rows = []
for r in tags:
    d = r["file"].replace(".mp4", "")
    p = pix.get(d, {}).get(str(r["t"]))
    if not p: continue
    rows.append({**r, **p})
print("joined", len(rows), "of", len(tags))

def corr(a, b):
    n = len(a); ma = sum(a)/n; mb = sum(b)/n
    sa = math.sqrt(sum((x-ma)**2 for x in a)); sb = math.sqrt(sum((x-mb)**2 for x in b))
    if sa == 0 or sb == 0: return 0.0
    return sum((x-ma)*(y-mb) for x, y in zip(a, b))/(sa*sb)

land = [r["p_landscape"] for r in rows]; blk = [r["p_blocked"] for r in rows]
print("\np_landscape: min %.3f med %.3f mean %.3f max %.3f  >=0.5: %d" % (min(land), sorted(land)[len(land)//2], sum(land)/len(land), max(land), sum(1 for v in land if v >= 0.5)))
print("p_blocked  : min %.3f med %.3f mean %.3f max %.3f  >=0.5: %d" % (min(blk), sorted(blk)[len(blk)//2], sum(blk)/len(blk), max(blk), sum(1 for v in blk if v >= 0.5)))
print("\ncorrelations with p_blocked:")
for k in ["lapvar","edge","std","colorful","sat","mean","skin","bright","dark"]:
    print("   %-9s %+.3f" % (k, corr(blk, [r[k] for r in rows])))
print("correlations with p_landscape:")
for k in ["lapvar","edge","std","colorful","sat","mean","skin","bright","dark"]:
    print("   %-9s %+.3f" % (k, corr(land, [r[k] for r in rows])))

print("\n--- lowest p_blocked (most likely clear scenery) ---")
s = sorted(rows, key=lambda r: r["p_blocked"])[:12]
print("file                  t  pBlk pLand pBlur pHand pCls scene        scP | lapvar  edge  std  color  mean")
for r in s:
    print("%-21s %3d  %.2f  %.2f  %.2f  %.2f  %.2f %-12s %.2f | %5.3f %5.3f %4.2f %5.3f %5.2f" % (
        r["file"].replace(".mp4",""), r["t"], r["p_blocked"], r["p_landscape"], r["p_blurry"], r["p_hand"], r["p_closeup"],
        r["scene"], r["scene_p"], r["lapvar"], r["edge"], r["std"], r["colorful"], r["mean"]))
print("\n--- highest p_blocked ---")
s = sorted(rows, key=lambda r: -r["p_blocked"])[:12]
for r in s:
    print("%-21s %3d  %.2f  %.2f  %.2f  %.2f  %.2f %-12s %.2f | %5.3f %5.3f %4.2f %5.3f %5.2f" % (
        r["file"].replace(".mp4",""), r["t"], r["p_blocked"], r["p_landscape"], r["p_blurry"], r["p_hand"], r["p_closeup"],
        r["scene"], r["scene_p"], r["lapvar"], r["edge"], r["std"], r["colorful"], r["mean"]))

print("\n--- scene distribution ---")
from collections import Counter
c = Counter(r["scene"] for r in rows)
for k, v in c.most_common(): print("   %-10s %3d" % (k, v))
print("\n--- class argmax distribution ---")
import collections
def argmaxcls(r):
    d = {"landscape": r["p_landscape"], "hand": r["p_hand"], "fabric": r["p_fabric"], "blurry": r["p_blurry"], "closeup": r["p_closeup"]}
    return max(d, key=d.get)
c2 = Counter(argmaxcls(r) for r in rows)
for k, v in c2.most_common(): print("   %-10s %3d" % (k, v))
