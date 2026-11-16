
import json, os, collections
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pf = json.load(open(os.path.join(V,"per_file.json"), encoding="utf-8"))
sm = json.load(open(os.path.join(V,"summary.json"), encoding="utf-8"))
cands = json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8"))

# blocked segments under strict definition (hand/fabric only)
def segs(cond, minlen=2):
    out=[]
    for f in sorted(tags):
        cur=[]
        for r in tags[f]:
            if cond(r): cur.append(r)
            else:
                if len(cur)>=minlen: out.append((f,cur[0]["t"],cur[-1]["t"],len(cur)))
                cur=[]
        if len(cur)>=minlen: out.append((f,cur[0]["t"],cur[-1]["t"],len(cur)))
    return out
spec = segs(lambda r: r["p_blocked"]>0.5)
strict = segs(lambda r: max(r["p_hand"], r["p_fabric"])>0.5)
fabric_hand = segs(lambda r: (r["p_hand"]+r["p_fabric"])>0.5)
print("spec (max hand,fabric,closeup): %d segs / %d s" % (len(spec), sum(s[3] for s in spec)))
print("strict (max hand,fabric)     : %d segs / %d s" % (len(strict), sum(s[3] for s in strict)))
print("sum hand+fabric > 0.5        : %d segs / %d s" % (len(fabric_hand), sum(s[3] for s in fabric_hand)))

dead = [r for r in pf if r["landscape_ratio"] < 0.05]
print("\nfiles with landscape_ratio<0.05 (%d files, %d s):" % (len(dead), sum(r["frames"] for r in dead)))
for r in sorted(dead, key=lambda r: r["landscape_ratio"]):
    print("  %-12s n=%3d ratio=%.2f meanL=%.3f blk=%.3f hand=%.3f fab=%.3f close=%.3f blur=%.3f cand=%ds" % (
        r["file"].replace(".mp4",""), r["frames"], r["landscape_ratio"], r["mean_p_landscape"],
        r["mean_p_blocked"], r["mean_p_hand"], r["mean_p_fabric"], r["mean_p_closeup"], r["mean_p_blurry"], r["candidate_secs"]))
best = sorted(pf, key=lambda r: -r["landscape_ratio"])[:6]
print("\nbest files:")
for r in best:
    print("  %-12s ratio=%.2f meanL=%.3f medL=%.3f blk=%.3f blur=%.3f cand=%3ds/%d段 scene=%s" % (
        r["file"].replace(".mp4",""), r["landscape_ratio"], r["mean_p_landscape"], r["median_p_landscape"],
        r["mean_p_blocked"], r["mean_p_blurry"], r["candidate_secs"], r["candidate_count"], r["top_scene"]))
print("\ntop candidates by detail_score:")
for c in sorted(cands, key=lambda c: -c["detail_score"])[:8]:
    print("  %-12s %3d-%3d L=%.3f detail=%.2f scene=%s blank=%s" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["mean_p_landscape"], c["detail_score"], c["scene"], c["blank_sky_suspect"]))
print("\nlongest candidates:")
for c in sorted(cands, key=lambda c: -c["dur"])[:8]:
    print("  %-12s %3d-%3d dur=%3d L=%.3f blk=%.3f scene=%s blank=%s" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["dur"], c["mean_p_landscape"], c["mean_p_blocked"], c["scene"], c["blank_sky_suspect"]))
