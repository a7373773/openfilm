
# -*- coding: utf-8 -*-
"""Aggregate CLIP frame tags into tags.json / per_file.json / candidates.json / summary.json."""
import json, os, statistics as st
from collections import Counter, defaultdict

V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
ND = os.path.join(V, "tags.json.ndjson")
PIX = os.path.join(V, "pixstats.json")
MIN_SEG = 3          # candidate min length (s)
BLOCK_MIN = 2        # blocked segment min length (s)
BLOCK_THRESH = 0.5
CAND_REL = 0.10      # above file median
CAND_BLOCK = 0.35

recs = defaultdict(list)
with open(ND, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line: continue
        r = json.loads(line)
        recs[r["file"]].append(r)

pix = {}
if os.path.exists(PIX):
    pix = json.load(open(PIX, encoding="utf-8"))

for f in recs:
    recs[f].sort(key=lambda r: r["t"])

# recompute p_blocked = max(hand, fabric, closeup)  (lead's definition, no blurry)
allframes = []
for f, rows in recs.items():
    for r in rows:
        r["p_blocked"] = round(max(r["p_hand"], r["p_fabric"], r["p_closeup"]), 4)
        allframes.append(r)

land = sorted(r["p_landscape"] for r in allframes)
def pctile(sorted_vals, q):
    if not sorted_vals: return 0.0
    k = (len(sorted_vals)-1) * q
    lo = int(k); hi = min(lo+1, len(sorted_vals)-1)
    return sorted_vals[lo] + (sorted_vals[hi]-sorted_vals[lo])*(k-lo)

dec = {f"p{int(q*100)}": round(pctile(land, q), 4) for q in (0.1, 0.25, 0.5, 0.75, 0.9)}
mean_land = sum(land)/len(land)
# empirical CDF lookup for percentile of a value
import bisect
def pct_rank(v):
    return round(bisect.bisect_right(land, v) / len(land), 4)

# ---- per file aggregates
per_file = []
for f in sorted(recs):
    rows = recs[f]
    L = [r["p_landscape"] for r in rows]; B = [r["p_blocked"] for r in rows]
    BL = [r["p_blurry"] for r in rows]; CU = [r["p_closeup"] for r in rows]
    med = st.median(L)
    scene_c = Counter(r["scene"] for r in rows)
    top_scene, top_n = scene_c.most_common(1)[0]
    per_file.append(dict(
        file=f, frames=len(rows), secs=len(rows),
        mean_p_landscape=round(sum(L)/len(L), 4), median_p_landscape=round(med, 4),
        mean_p_blocked=round(sum(B)/len(B), 4), median_p_blocked=round(st.median(B), 4),
        mean_p_blurry=round(sum(BL)/len(BL), 4), mean_p_closeup=round(sum(CU)/len(CU), 4),
        landscape_ratio=round(sum(1 for v in L if v >= 0.5)/len(L), 4),
        landscape_ratio_30=round(sum(1 for v in L if v >= 0.3)/len(L), 4),
        blocked_ratio=round(sum(1 for v in B if v >= 0.5)/len(B), 4),
        top_scene=top_scene, top_scene_ratio=round(top_n/len(rows), 4),
        scene_mix={k: round(v/len(rows), 3) for k, v in scene_c.most_common()},
        p_landscape_max=round(max(L), 4), p_landscape_min=round(min(L), 4),
    ))

# ---- tags.json (with relative ranking info)
tags_out = {}
for f in sorted(recs):
    rows = recs[f]
    med = st.median([r["p_landscape"] for r in rows])
    out = []
    for r in rows:
        out.append(dict(
            t=r["t"], p_landscape=r["p_landscape"], p_blocked=r["p_blocked"],
            p_hand=r["p_hand"], p_fabric=r["p_fabric"], p_closeup=r["p_closeup"], p_blurry=r["p_blurry"],
            scene=r["scene"], scene_p=r["scene_p"],
            p_landscape_pct=pct_rank(r["p_landscape"]),
            p_landscape_rel=round(r["p_landscape"] - med, 4),
        ))
    tags_out[f] = out
with open(os.path.join(V, "tags.json"), "w", encoding="utf-8") as fh:
    json.dump(tags_out, fh, ensure_ascii=False)

# ---- blocked segments (>=2 s consecutive p_blocked > 0.5)
blocked_segments = []
for f in sorted(recs):
    rows = recs[f]
    seg = []
    for r in rows:
        if r["p_blocked"] > BLOCK_THRESH:
            seg.append(r)
        else:
            if len(seg) >= BLOCK_MIN:
                blocked_segments.append(dict(file=f, start_t=seg[0]["t"], end_t=seg[-1]["t"],
                    dur=len(seg), mean_p_blocked=round(sum(x["p_blocked"] for x in seg)/len(seg), 3),
                    max_p_blocked=round(max(x["p_blocked"] for x in seg), 3)))
            seg = []
    if len(seg) >= BLOCK_MIN:
        blocked_segments.append(dict(file=f, start_t=seg[0]["t"], end_t=seg[-1]["t"],
            dur=len(seg), mean_p_blocked=round(sum(x["p_blocked"] for x in seg)/len(seg), 3),
            max_p_blocked=round(max(x["p_blocked"] for x in seg), 3)))
blocked_segments.sort(key=lambda s: (s["file"], s["start_t"]))
blocked_secs = sum(s["dur"] for s in blocked_segments)

# ---- candidates: >=3 s, mean p_landscape >= file median + 0.10, mean p_blocked < 0.35
candidates = []
for f in sorted(recs):
    rows = recs[f]
    med = st.median([r["p_landscape"] for r in rows])
    thresh = med + CAND_REL
    seg = []
    def flush(seg):
        if len(seg) < MIN_SEG: return
        mL = sum(x["p_landscape"] for x in seg)/len(seg)
        mB = sum(x["p_blocked"] for x in seg)/len(seg)
        if mL < thresh or mB >= CAND_BLOCK: return
        sc = Counter(x["scene"] for x in seg).most_common(1)[0]
        sc_p = sum(x["scene_p"] for x in seg if x["scene"] == sc[0])/max(1, sum(1 for x in seg if x["scene"] == sc[0]))
        candidates.append(dict(file=f, start_t=seg[0]["t"], end_t=seg[-1]["t"], dur=len(seg),
            mean_p_landscape=round(mL, 4), mean_p_blocked=round(mB, 4),
            min_p_landscape=round(min(x["p_landscape"] for x in seg), 4),
            scene=sc[0], scene_p=round(sc_p, 3), scene_ratio=round(sc[1]/len(seg), 3),
            file_median_p_landscape=round(med, 4)))
    for r in rows:
        if r["p_landscape"] >= thresh and r["p_blocked"] < CAND_BLOCK:
            seg.append(r)
        else:
            flush(seg); seg = []
    flush(seg)
candidates.sort(key=lambda c: -c["mean_p_landscape"])
with open(os.path.join(V, "candidates.json"), "w", encoding="utf-8") as fh:
    json.dump(candidates, fh, ensure_ascii=False, indent=1)
with open(os.path.join(V, "per_file.json"), "w", encoding="utf-8") as fh:
    json.dump(per_file, fh, ensure_ascii=False, indent=1)

# ---- spot checks on known-suspect files using pixel stats
def pixget(f, t):
    d = f.replace(".mp4", "")
    return pix.get(d, {}).get(str(t))

summary = dict(
    total_frames=len(allframes), files=len(recs), deciles=dec, mean=round(mean_land, 4),
    landscape_ge_05=sum(1 for v in land if v >= 0.5),
    blocked_segments=blocked_segments, blocked_secs=blocked_secs,
    candidates=len(candidates),
    candidate_secs=sum(c["dur"] for c in candidates),
    per_file=per_file,
)
with open(os.path.join(V, "summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=1)

print("=== global p_landscape distribution ===")
print("n=%d mean=%.3f  p10=%.3f p25=%.3f p50=%.3f p75=%.3f p90=%.3f  >=0.5: %d (%.1f%%)" % (
    len(land), mean_land, dec["p10"], dec["p25"], dec["p50"], dec["p75"], dec["p90"],
    summary["landscape_ge_05"], 100*summary["landscape_ge_05"]/len(land)))
print("\n=== files sorted by landscape_ratio (lowest 8 = likely blocked/dead) ===")
for r in sorted(per_file, key=lambda r: r["landscape_ratio"])[:8]:
    print("%-14s n=%3d ratio=%.2f meanL=%.3f medL=%.3f meanBlk=%.3f meanBlur=%.3f top=%s" % (
        r["file"].replace(".mp4",""), r["frames"], r["landscape_ratio"], r["mean_p_landscape"],
        r["median_p_landscape"], r["mean_p_blocked"], r["mean_p_blurry"], r["top_scene"]))
print("\n=== files sorted by landscape_ratio (highest 8 = best raw material) ===")
for r in sorted(per_file, key=lambda r: -r["landscape_ratio"])[:8]:
    print("%-14s n=%3d ratio=%.2f meanL=%.3f medL=%.3f meanBlk=%.3f top=%s" % (
        r["file"].replace(".mp4",""), r["frames"], r["landscape_ratio"], r["mean_p_landscape"],
        r["median_p_landscape"], r["mean_p_blocked"], r["top_scene"]))
print("\n=== blocked segments: %d segments, %d seconds ===" % (len(blocked_segments), blocked_secs))
for s in blocked_segments[:25]:
    print("  %-14s %4d-%4d (%2ds) meanBlk=%.2f" % (s["file"].replace(".mp4",""), s["start_t"], s["end_t"], s["dur"], s["mean_p_blocked"]))
print("\n=== candidates: %d segments, %d seconds ===" % (len(candidates), summary["candidate_secs"]))
for c in candidates[:20]:
    print("  %-14s %4d-%4d (%3ds) L=%.3f blk=%.3f scene=%s(%.2f)" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["dur"], c["mean_p_landscape"], c["mean_p_blocked"], c["scene"], c["scene_p"]))

print("\n=== spot check REC-0004-A first 20s ===")
for t in range(1, 21):
    r = next((x for x in recs.get("REC-0004-A.mp4", []) if x["t"] == t), None)
    p = pixget("REC-0004-A.mp4", t)
    if r:
        print("  t=%2d L=%.2f blk=%.2f blur=%.2f scene=%-9s | lapvar=%.3f edge=%.3f flat=%.2f sky=%.2f" % (
            t, r["p_landscape"], r["p_blocked"], r["p_blurry"], r["scene"],
            p["lapvar"] if p else -1, p["edge"] if p else -1, p["flatfrac"] if p else -1, p["skyfrac"] if p else -1))
print("\n=== p_closeup on road-scene frames (check ground/road confusion) ===")
roads = [x for x in allframes if x["scene"] == "road"]
if roads:
    print("n=%d  mean p_closeup=%.3f  frac closeup>0.35: %.2f" % (len(roads), sum(x["p_closeup"] for x in roads)/len(roads), sum(1 for x in roads if x["p_closeup"]>0.35)/len(roads)))
