# -*- coding: utf-8 -*-
"""02_pick: one shot per subject cluster, beat-aligned, transition mix capped.
usage: python 02_pick.py <workdir> [target_seconds]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

WORK = sys.argv[1]
TARGET = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
IDX = json.load(open(os.path.join(WORK, "index.json"), encoding="utf-8"))
B = RULES["beat"]["beat_unit_s"]
clips = {c["file"]: c for c in IDX["clips"]}

cands = []
for cl in IDX["clusters"]:
    best = clips[cl["best"]]
    if best.get("quality", 0) < 8: continue
    d_src = min(5.0, max(2.5, best["dur"] - 0.4))
    start, _ = best_window(best["rows"], d_src)
    cands.append(dict(file=best["file"], cluster=cl["id"], q=best["quality"],
                      faces=best.get("faces", 0), start=start, dur_src=best["dur"],
                      tc=best.get("tc_sec", 0), bright=best.get("bright", 0)))
cands.sort(key=lambda c: c["tc"])

def beats_for(c):
    d = 5.0 if c["dur_src"] >= 6 else 4.375
    if c["faces"] > 0.5: d += 0.625
    return int(round(d / B))

for c in cands: c["dur"] = beats_for(c) * B

# trim to target: drop the weakest shots that are close in time to a neighbour
def total(cs): return sum(c["dur"] for c in cs) - (len(cs)-1)*B
while total(cands) > TARGET and len(cands) > 8:
    worst = min(cands, key=lambda c: c["q"] + (1.0 if c["dur"] >= 5 else 0))
    cands.remove(worst)

# transitions: <= max ratio directional, rest crossfade
DIRS = ["smoothleft", "smoothright", "smoothup"]
out = []
budget = int(len(cands) * RULES["transitions"]["directional_ratio_max"])
for i, c in enumerate(cands):
    if i > 0 and budget > 0 and i % 4 == 0:
        xf = DIRS[(i//4) % len(DIRS)]; budget -= 1
    elif i > 0 and i % 7 == 0:
        xf = "dissolve"
    else:
        xf = RULES["transitions"]["default"]
    out.append(dict(i=i, file=c["file"], cluster=c["cluster"], q=round(c["q"], 1),
                    start=round(c["start"], 2), dur=c["dur"], xf=xf, note="cluster C%02d" % c["cluster"]))

pos, t = [], 0.0
for s in out:
    pos.append(round(t, 3)); t += s["dur"] - RULES["beat"]["transition_s"]
total_s = t + RULES["beat"]["transition_s"]
json.dump(dict(shots=out, pos=pos, total=round(total_s, 3)),
          open(os.path.join(WORK, "pick.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("picked %d shots, %.1fs (%.1f bars)  target %.0fs" % (len(out), total_s, total_s/B/4, TARGET))
for s, p in zip(out, pos):
    print("%02d %6.2f %s cluster=C%02d q=%5.1f d=%4.2f %s" % (s["i"], p, s["file"], s["cluster"], s["q"], s["dur"], s["xf"]))