
# -*- coding: utf-8 -*-
"""Aggregate hike tags -> per_clip.json (+ summary.json). v2: sky-aware flags."""
import json, os, statistics as st, collections
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pix  = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))

def pget(clip, t):
    return pix.get(clip.replace(".mp4",""), {}).get(str(int(round(t/0.5))+1))

def ranges(clip, cond, minframes=2):
    out=[]; cur=[]
    for r in tags[clip]:
        if cond(r): cur.append(r["t"])
        else:
            if len(cur)>=minframes: out.append([cur[0], round(cur[-1]+0.5,1)])
            cur=[]
    if len(cur)>=minframes: out.append([cur[0], round(cur[-1]+0.5,1)])
    return out

per = {}
for clip in sorted(tags):
    rr = tags[clip]; n = len(rr)
    px = [pget(clip, r["t"]) for r in rr]; px = [x for x in px if x]
    g = lambda k: sum(r[k] for r in rr)/n
    ratio = lambda k, th: sum(1 for r in rr if r[k] >= th)/n
    pm = lambda k: sum(x[k] for x in px)/len(px) if px else None
    p = dict(
        file=clip, frames=n, duration=round(n*0.5, 1),
        mean_p_person=round(g("p_person"),3), mean_p_people=round(g("p_people"),3),
        mean_p_back=round(g("p_back"),3), mean_p_back_far=round(g("p_back_far"),3),
        mean_p_back_close=round(g("p_back_close"),3), mean_p_facing=round(g("p_facing"),3),
        mean_p_landscape=round(g("p_landscape"),3), mean_p_wide_vista=round(g("p_wide_vista"),3),
        mean_p_blocked=round(g("p_blocked"),3), mean_p_ground=round(g("p_ground"),3),
        mean_p_blurry=round(g("p_blurry"),3), mean_p_clear=round(g("p_clear"),3),
        person_ratio=round(ratio("p_person",0.5),3), back_ratio=round(ratio("p_back",0.5),3),
        back_close_ratio=round(ratio("p_back_close",0.5),3), vista_ratio=round(ratio("p_wide_vista",0.5),3),
        blocked_ratio=round(ratio("p_blocked",0.5),3), ground_ratio=round(ratio("p_ground",0.5),3),
        blur_ratio=round(ratio("p_blurry",0.7),3),
        dominant_view=collections.Counter(r["view"] for r in rr).most_common(1)[0][0],
        dominant_scene=collections.Counter(r["scene"] for r in rr).most_common(1)[0][0],
        scene_mix={k: round(v/n,3) for k,v in collections.Counter(r["scene"] for r in rr).most_common()},
        obj_lapvar=round(pm("lapvar"),4) if px else None, obj_edge=round(pm("edge"),3) if px else None,
        obj_skyfrac=round(pm("skyfrac"),3) if px else None, obj_greenfrac=round(pm("greenfrac"),3) if px else None,
        obj_skin=round(pm("skin"),3) if px else None, obj_topLap=round(pm("topLap"),4) if px else None,
        obj_botLap=round(pm("botLap"),4) if px else None, obj_colorful=round(pm("colorful"),3) if px else None,
        obj_mean=round(pm("mean"),3) if px else None,
    )
    per[clip] = p

for clip, p in per.items():
    f = []
    lap = p["obj_lapvar"] or 1.0; sky = p["obj_skyfrac"] or 0.0
    bot = p["obj_botLap"] or 1.0
    if p["person_ratio"] >= 0.7: f.append("人物主导")
    elif p["person_ratio"] >= 0.3: f.append("人物/风景混合")
    else: f.append("基本无人")
    if p["back_ratio"] >= 0.6 and p["mean_p_landscape"] >= 0.45: f.append("跟拍背影")
    if p["back_close_ratio"] >= 0.3: f.append("背包怼镜头")
    if p["blocked_ratio"] >= 0.2: f.append("遮挡")
    if p["ground_ratio"] >= 0.2: f.append("对地")
    if p["vista_ratio"] >= 0.25 or (p["dominant_scene"] == "summit" and p["mean_p_landscape"] >= 0.8): f.append("大远景/山顶")
    if lap < 0.006 and sky < 0.4: f.append("整体偏糊")
    if p["blur_ratio"] >= 0.85 and lap < 0.010 and sky < 0.4: f.append("糊镜头多")
    if bot < 0.004 and lap < 0.006: f.append("低细节/雾化")
    if sky >= 0.85 and bot < 0.003: f.append("纯天空/低内容")
    p["flags"] = f
    p["is_waste"] = any(x in f for x in ("遮挡","背包怼镜头","对地","糊镜头多","整体偏糊"))
    p["blocked_ranges"] = ranges(clip, lambda r: r["p_blocked"] >= 0.5)
    p["motion_ranges"] = ranges(clip, lambda r: r["p_back"] >= 0.5 and r["p_blocked"] < 0.35 and r["p_landscape"] >= 0.5, 3)
    p["vista_ranges"] = ranges(clip, lambda r: r["p_wide_vista"] >= 0.4)
    p["motion_score"] = round(0.4*p["mean_p_back_far"] + 0.2*p["mean_p_person"] + 0.3*p["mean_p_landscape"]
                              - 0.3*p["mean_p_blocked"] - 0.2*max(0.0, p["blur_ratio"]-0.6), 3)
    p["ending_score"] = round(0.45*p["mean_p_wide_vista"] + 0.30*p["mean_p_landscape"] + 0.25*min(1.0, bot/0.02), 3)

json.dump(list(per.values()), open(os.path.join(V,"per_clip.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

allf = [r for c in tags for r in tags[c]]
def mean(k): return sum(r[k] for r in allf)/len(allf)
summary = dict(clips=len(tags), frames=len(allf), duration=round(len(allf)*0.5,1),
    mean=dict(p_person=round(mean("p_person"),3), p_people=round(mean("p_people"),3),
              p_back=round(mean("p_back"),3), p_landscape=round(mean("p_landscape"),3),
              p_wide_vista=round(mean("p_wide_vista"),3), p_blocked=round(mean("p_blocked"),3),
              p_ground=round(mean("p_ground"),3), p_blurry=round(mean("p_blurry"),3), p_clear=round(mean("p_clear"),3)),
    scenes=dict(collections.Counter(r["scene"] for r in allf)),
    views=dict(collections.Counter(r["view"] for r in allf)),
    person_frames=sum(1 for r in allf if r["p_person"]>=0.5),
    back_frames=sum(1 for r in allf if r["p_back"]>=0.5),
    vista_frames=sum(1 for r in allf if r["p_wide_vista"]>=0.5),
    blocked_frames=sum(1 for r in allf if r["p_blocked"]>=0.5),
    waste_clips=sum(1 for p in per.values() if p["is_waste"]))
json.dump(summary, open(os.path.join(V,"summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("clips", len(per), "frames", len(allf))
print("\n-- ending candidates with objective detail --")
print("  %-11s %3s %5s | vista land person | lapvar  topLap botLap colorful sky  flags" % ("clip","n","dur"))
for p in sorted(per.values(), key=lambda p: -p["ending_score"])[:12]:
    print("  %-11s %3d %5.1f | %.2f %.2f %.2f | %.4f %.4f %.4f %.3f %.2f  %s" % (
        p["file"].replace(".mp4",""), p["frames"], p["duration"], p["mean_p_wide_vista"], p["mean_p_landscape"], p["mean_p_person"],
        p["obj_lapvar"], p["obj_topLap"], p["obj_botLap"], p["obj_colorful"], p["obj_skyfrac"], ",".join(p["flags"])))
print("\n-- waste clips --")
for p in sorted([p for p in per.values() if p["is_waste"]], key=lambda p: -p["mean_p_blocked"]):
    print("  %-11s block=%.2f bagclose=%.2f ground=%.2f lapvar=%.4f flags=%s ranges=%s" % (
        p["file"].replace(".mp4",""), p["mean_p_blocked"], p["mean_p_back_close"], p["mean_p_ground"], p["obj_lapvar"],
        ",".join(p["flags"]), p["blocked_ranges"]))
print("\n-- motion windows sample --")
for p in sorted(per.values(), key=lambda p: -p["motion_score"])[:8]:
    print("  %-11s motion=%.2f ranges=%s" % (p["file"].replace(".mp4",""), p["motion_score"], p["motion_ranges"]))
