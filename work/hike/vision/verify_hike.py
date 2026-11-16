
# -*- coding: utf-8 -*-
import json, os, math
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pc = {p["file"]: p for p in json.load(open(os.path.join(V,"per_clip.json"), encoding="utf-8"))}
ok = True
def fail(m):
    global ok; ok=False; print("  FAIL:", m)

print("== coverage / consistency ==")
FR = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis\frames"
dirs = sorted(d for d in os.listdir(FR) if os.path.isdir(os.path.join(FR,d)))
print("  clip dirs:", len(dirs), "| tags keys:", len(tags))
if len(dirs) != len(tags): fail("clip count mismatch")
tot = 0
for d in dirs:
    n = len([f for f in os.listdir(os.path.join(FR,d)) if f.endswith(".jpg")])
    tot += n
    key = d + ".mp4"
    if key not in tags: fail("missing "+key); continue
    rr = tags[key]
    if len(rr) != n: fail("%s frames %d != %d" % (d, len(rr), n))
    ts = [r["t"] for r in rr]
    exp = [round((i)*0.5,1) for i in range(n)]
    if ts != exp: fail("%s t mismatch: %s vs %s" % (d, ts[:5], exp[:5]))
    for r in rr:
        if abs((r["p_person"] + r["p_nobody"]) - 1.0) > 1e-3: fail("%s t=%s person+nobody != 1" % (d, r["t"])); break
        if abs(r["p_back"] - (r["p_back_far"] + r["p_back_close"])) > 1e-3: fail("%s back sum %.3f vs %.3f" % (d, r["p_back"], r["p_back_far"] + r["p_back_close"])); break
        for k in ["p_person","p_people","p_landscape","p_blocked","p_ground","p_blurry","p_clear","p_wide_vista"]:
            if not (0 <= r[k] <= 1): fail("%s t=%s %s out of range" % (d, r["t"], k))
        if not isinstance(r.get("p_landscape_pct"), (int,float)): fail("missing pct"); break
print("  total frames:", tot)

print("\n== ending candidates: objective detail ==")
print("  %-11s %5s %6s %8s %8s %8s %8s %8s" % ("clip","frames","lapvar","edge","skyfrac","green","vista","land"))
for c in ["C1905S03","C1908S03","C1907S03","C1906S03","C1883S03","C1894S03","C1881S03","C1882S03","C1895S03"]:
    p = pc[c + ".mp4"]
    print("  %-11s %5d %8.4f %8.3f %8.2f %8.2f %8.2f %8.2f" % (c, p["frames"], p["obj_lapvar"], p["obj_edge"], p["obj_skyfrac"], p["obj_greenfrac"], p["mean_p_wide_vista"], p["mean_p_landscape"]))

print("\n== all clips with obj_lapvar<0.006 (current 'blurry' flags) ==")
for f,p in sorted(pc.items(), key=lambda kv: kv[1]["obj_lapvar"] or 9):
    if (p["obj_lapvar"] or 9) < 0.006:
        print("  %-11s lapvar=%.4f sky=%.2f edge=%.3f vista=%.2f land=%.2f flags=%s" % (
            f.replace(".mp4",""), p["obj_lapvar"], p["obj_skyfrac"], p["obj_edge"], p["mean_p_wide_vista"], p["mean_p_landscape"], ",".join(p["flags"])))
print("\nRESULT:", "ALL OK" if ok else "ISSUES FOUND")
