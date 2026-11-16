
# -*- coding: utf-8 -*-
import json, os
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
pc = {p["file"]: p for p in json.load(open(os.path.join(V,"per_clip.json"), encoding="utf-8"))}
print("== motion top 12 (with ranges) ==")
for p in sorted(pc.values(), key=lambda p: -p["motion_score"])[:12]:
    print("  %-9s %5.1fs motion=%.2f back=%.2f land=%.2f block=%.2f lapvar=%.4f ranges=%s" % (
        p["file"].replace(".mp4",""), p["duration"], p["motion_score"], p["mean_p_back"], p["mean_p_landscape"], p["mean_p_blocked"], p["obj_lapvar"], p["motion_ranges"]))
print("\n== ending: crisp top 6 ==")
crisp = [p for p in pc.values() if (p["obj_lapvar"] or 0) >= 0.008 and (p["obj_botLap"] or 0) >= 0.015]
for p in sorted(crisp, key=lambda p: -p["ending_score"])[:6]:
    print("  %-9s %5.1fs ending=%.2f vista=%.2f land=%.2f lapvar=%.4f botLap=%.4f color=%.3f person=%.2f scene=%s" % (
        p["file"].replace(".mp4",""), p["duration"], p["ending_score"], p["mean_p_wide_vista"], p["mean_p_landscape"],
        p["obj_lapvar"], p["obj_botLap"], p["obj_colorful"], p["mean_p_person"], p["dominant_scene"]))
print("\n== haze/blank clips (lapvar<0.004 and botLap<0.005) ==")
for p in sorted(pc.values(), key=lambda p: (p["obj_lapvar"] or 0)):
    if (p["obj_lapvar"] or 9) < 0.004 and (p["obj_botLap"] or 9) < 0.005:
        print("  %-9s %5.1fs lapvar=%.4f botLap=%.4f color=%.3f sky=%.2f vista=%.2f land=%.2f flags=%s" % (
            p["file"].replace(".mp4",""), p["duration"], p["obj_lapvar"], p["obj_botLap"], p["obj_colorful"],
            p["obj_skyfrac"], p["mean_p_wide_vista"], p["mean_p_landscape"], ",".join(p["flags"])))
print("\n== waste (is_waste) ==")
for p in sorted([x for x in pc.values() if x["is_waste"]], key=lambda p: -p["mean_p_blocked"]):
    print("  %-9s block=%.2f bag=%.2f ground=%.2f lapvar=%.4f flags=%s" % (
        p["file"].replace(".mp4",""), p["mean_p_blocked"], p["mean_p_back_close"], p["mean_p_ground"], p["obj_lapvar"], ",".join(p["flags"])))
print("\n== empty (person_ratio<0.5) ==")
for p in sorted(pc.values(), key=lambda p: p["mean_p_person"]):
    if p["person_ratio"] < 0.5:
        print("  %-9s %5.1fs person=%.2f land=%.2f lapvar=%.4f scene=%s flags=%s" % (
            p["file"].replace(".mp4",""), p["duration"], p["mean_p_person"], p["mean_p_landscape"], p["obj_lapvar"], p["dominant_scene"], ",".join(p["flags"])))
print("\n== counts ==")
print("  clips:", len(pc), "| person_ratio>=0.7:", sum(1 for p in pc.values() if p["person_ratio"]>=0.7),
      "| waste:", sum(1 for p in pc.values() if p["is_waste"]), "| ending crisp:", len(crisp))
