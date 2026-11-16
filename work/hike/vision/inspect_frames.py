
# -*- coding: utf-8 -*-
import json, os
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
def show(clip):
    print("\n== %s ==" % clip)
    print("  t    vista land person block | lapvar  edge   topLap botLap sky   green  mean  colorful")
    for r in tags[clip]:
        seq = int(round(r["t"]/0.5))+1
        p = pix[clip.replace(".mp4","")].get(str(seq))
        print("  %4.1f %5.2f %5.2f %5.2f %5.2f | %.4f %.3f  %.4f %.4f %.2f %.2f %.2f %.3f" % (
            r["t"], r["p_wide_vista"], r["p_landscape"], r["p_person"], r["p_blocked"],
            p["lapvar"], p["edge"], p["topLap"], p["botLap"], p["skyfrac"], p["greenfrac"], p["mean"], p["colorful"]))
for c in ["C1905S03.mp4","C1908S03.mp4","C1882S03.mp4","C1895S03.mp4"]:
    show(c)
