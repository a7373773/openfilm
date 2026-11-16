# -*- coding: utf-8 -*-
"""16_retime: re-snap an existing EDL to a new tempo grid + target length."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
WORK = sys.argv[1]
BEAT = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8      # 75 bpm -> 0.8 s
XFD  = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
TARGET = float(sys.argv[4]) if len(sys.argv) > 4 else 125.0
edl = json.load(open(os.path.join(WORK, "edl.json"), encoding="utf-8"))
shots = edl["shots"]

for s in shots:
    n = max(3, int(round(s["dur"] / BEAT)))
    s["dur"] = round(n*BEAT, 3)
    s["xfd"] = XFD
    s["src"] = round(s["dur"]*s["speed"], 3)

def total(cs): return sum(c["dur"] for c in cs) - (len(cs)-1)*XFD
# trim: shave one beat off the longest wide shots first, never below 3 beats
order = sorted(range(len(shots)), key=lambda i: -shots[i]["dur"])
while total(shots) > TARGET and any(s["dur"] > 3*BEAT for s in shots):
    for i in order:
        if shots[i]["dur"] > 3*BEAT:
            shots[i]["dur"] = round(shots[i]["dur"] - BEAT, 3)
            shots[i]["src"] = round(shots[i]["dur"]*shots[i]["speed"], 3)
            break

pos, t = [], 0.0
for s in shots:
    pos.append(round(t, 4)); t += s["dur"] - XFD
T = round(t + XFD, 3)
for i, s in enumerate(shots):
    s["i"] = i; s["xf"] = s.get("xf", "fade")
    s["warm"] = round(i/max(1, len(shots)-1), 3)
edl.update(shots=shots, pos=pos, total=T, beat=BEAT, xfade={k: XFD for k in set(s["xf"] for s in shots)})
json.dump(edl, open(os.path.join(WORK, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("retimed: %d shots, %.2fs = %s, beat %.3f, xfade %.3f" % (len(shots), T, mmss(T), BEAT, XFD))
for s, p in zip(shots, pos):
    print("%02d %6.2f %s d=%4.2f b=%.1f" % (s["i"], p, s["file"], s["dur"], s["dur"]/BEAT))