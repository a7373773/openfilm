
# -*- coding: utf-8 -*-
"""Final artifacts: candidates.json / per_file.json / REPORT.md (+ summary.json)."""
import json, os, statistics as st, collections

V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = json.load(open(os.path.join(V, "tags.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V, "pixstats.json"), encoding="utf-8"))
aux = json.load(open(os.path.join(V, "aux.json"), encoding="utf-8"))
sm = json.load(open(os.path.join(V, "summary.json"), encoding="utf-8"))

MIN_SEG, CAND_REL, CAND_BLOCK = 3, 0.10, 0.35

def pget(f, t): return pix.get(f.replace(".mp4", ""), {}).get(str(t))
def aget(f, t): return aux.get(f, {}).get(str(t))

def seg_stats(f, a, b):
    fr = [pget(f, t) for t in range(a, b+1)]; fr = [x for x in fr if x]
    ax = [aget(f, t) for t in range(a, b+1)]; ax = [x for x in ax if x]
    d = {}
    for k in ["skyfrac","flatfrac","botLap","topLap","lapvar","colorful","greenfrac","edge","mean","std","skin"]:
        d[k] = round(sum(x[k] for x in fr)/len(fr), 4) if fr else None
    d["p_clear"] = round(sum(x["p_clear_scenery"] for x in ax)/len(ax), 4) if ax else None
    d["p_blank"] = round(sum(x["p_blank"] for x in ax)/len(ax), 4) if ax else None
    return d

# ---------------- candidates (lead's spec + objective/aux annotations)
cands = []
for f in sorted(tags):
    rows = tags[f]
    L = [r["p_landscape"] for r in rows]
    med = st.median(L); thresh = med + CAND_REL
    seg = []
    def flush(seg):
        if len(seg) < MIN_SEG: return
        mL = sum(x["p_landscape"] for x in seg)/len(seg)
        mB = sum(x["p_blocked"] for x in seg)/len(seg)
        if mL < thresh or mB >= CAND_BLOCK: return
        a, b = seg[0]["t"], seg[-1]["t"]
        sc = collections.Counter(x["scene"] for x in seg).most_common(1)[0]
        stt = seg_stats(f, a, b)
        blank = (stt["p_blank"] is not None and stt["p_blank"] >= 0.5) or (stt["skyfrac"] > 0.85 and stt["botLap"] < 0.012)
        cands.append(dict(file=f, start_t=a, end_t=b, dur=len(seg),
            mean_p_landscape=round(mL, 4), mean_p_blocked=round(mB, 4),
            min_p_landscape=round(min(x["p_landscape"] for x in seg), 4),
            scene=sc[0], scene_p=round(sum(x["scene_p"] for x in seg if x["scene"] == sc[0])/max(1, sum(1 for x in seg if x["scene"] == sc[0])), 3),
            scene_ratio=round(sc[1]/len(seg), 3),
            file_median_p_landscape=round(med, 4),
            blank_sky_suspect=blank,
            stats=stt,
            detail_score=round((min(1.0, stt["botLap"]/0.04)*0.4 + (1-min(1.0, stt["flatfrac"]/0.6))*0.3 + min(1.0, stt["edge"]/0.25)*0.3), 3)))
    for r in rows:
        if r["p_landscape"] >= thresh and r["p_blocked"] < CAND_BLOCK: seg.append(r)
        else: flush(seg); seg = []
    flush(seg)
cands.sort(key=lambda c: -c["mean_p_landscape"])
json.dump(cands, open(os.path.join(V, "candidates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------- per_file.json
per_file = []
for f in sorted(tags):
    rows = tags[f]
    L = [r["p_landscape"] for r in rows]; B = [r["p_blocked"] for r in rows]
    BL = [r["p_blurry"] for r in rows]; CU = [r["p_closeup"] for r in rows]
    H = [r["p_hand"] for r in rows]; FB = [r["p_fabric"] for r in rows]
    ax = [aget(f, r["t"]) for r in rows]; ax = [x for x in ax if x]
    blocked_secs = sum(s["dur"] for s in sm["blocked_segments"] if s["file"] == f)
    cand_here = [c for c in cands if c["file"] == f]
    scene_c = collections.Counter(r["scene"] for r in rows)
    per_file.append(dict(
        file=f, frames=len(rows), secs=len(rows),
        mean_p_landscape=round(sum(L)/len(L), 4), median_p_landscape=round(st.median(L), 4),
        mean_p_blocked=round(sum(B)/len(B), 4), median_p_blocked=round(st.median(B), 4),
        mean_p_blurry=round(sum(BL)/len(BL), 4),
        mean_p_hand=round(sum(H)/len(H), 4), mean_p_fabric=round(sum(FB)/len(FB), 4),
        mean_p_closeup=round(sum(CU)/len(CU), 4),
        mean_p_clear=round(sum(x["p_clear_scenery"] for x in ax)/len(ax), 4) if ax else None,
        mean_p_blank=round(sum(x["p_blank"] for x in ax)/len(ax), 4) if ax else None,
        landscape_ratio=round(sum(1 for v in L if v >= 0.5)/len(L), 4),
        landscape_ratio_30=round(sum(1 for v in L if v >= 0.3)/len(L), 4),
        blocked_ratio=round(sum(1 for v in B if v >= 0.5)/len(B), 4),
        blocked_secs=blocked_secs,
        candidate_secs=sum(c["dur"] for c in cand_here), candidate_count=len(cand_here),
        top_scene=scene_c.most_common(1)[0][0], top_scene_ratio=round(scene_c.most_common(1)[0][1]/len(rows), 3),
        p_landscape_max=round(max(L), 4), p_landscape_min=round(min(L), 4),
    ))
json.dump(per_file, open(os.path.join(V, "per_file.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------------- extra numbers for the report
def pctile(sv, q):
    k = (len(sv)-1)*q; lo = int(k); hi = min(lo+1, len(sv)-1)
    return sv[lo] + (sv[hi]-sv[lo])*(k-lo)
land_all = sorted(r["p_landscape"] for f in tags for r in tags[f])
blk_all = sorted(r["p_blocked"] for f in tags for r in tags[f])
dec = {("p%d" % (q*100)): round(pctile(land_all, q), 4) for q in (0.1,0.25,0.5,0.75,0.9)}
dec_blk = {("p%d" % (q*100)): round(pctile(blk_all, q), 4) for q in (0.1,0.25,0.5,0.75,0.9)}
dom = collections.Counter()
for f in tags:
    for r in tags[f]:
        if r["p_blocked"] > 0.5:
            comp = max([("hand", r["p_hand"]), ("fabric", r["p_fabric"]), ("closeup", r["p_closeup"])], key=lambda x: x[1])
            dom[comp[0]] += 1
summary = dict(total_frames=len(land_all), files=len(tags), deciles=dec, deciles_p_blocked=dec_blk,
    mean_p_landscape=round(sum(land_all)/len(land_all), 4),
    landscape_ge_05=sum(1 for v in land_all if v >= 0.5),
    landscape_ge_03=sum(1 for v in land_all if v >= 0.3),
    blocked_segments=sm["blocked_segments"], blocked_secs=sm["blocked_secs"],
    blocked_dominant=dict(dom),
    candidates=len(cands), candidate_secs=sum(c["dur"] for c in cands),
    candidates_blank_suspect=sum(1 for c in cands if c["blank_sky_suspect"]),
    per_file=per_file)
json.dump(summary, open(os.path.join(V, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("candidates:", len(cands), "secs:", sum(c["dur"] for c in cands), "blank_suspect:", summary["candidates_blank_suspect"])
print("deciles L:", dec)
print("deciles blocked:", dec_blk)
print("median landscape_ratio:", st.median([r["landscape_ratio"] for r in per_file]))
print("\nblank-sky suspects among candidates (top 12 by L):")
for c in cands[:12]:
    print("  %-12s %3d-%3d %s L=%.3f blank=%s(%.2f) clear=%.2f sky=%.2f botLap=%.4f detail=%.2f" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], "SUSPECT" if c["blank_sky_suspect"] else "       ",
        c["mean_p_landscape"], c["blank_sky_suspect"], c["stats"]["p_blank"], c["stats"]["p_clear"],
        c["stats"]["skyfrac"], c["stats"]["botLap"], c["detail_score"]))
