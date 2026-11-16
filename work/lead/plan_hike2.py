# -*- coding: utf-8 -*-
"""Build the ordered 3-min hiking EDL (v3): analyst keep windows + CLIP blocked filtering."""
import json, os
import numpy as np
from PIL import Image

WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
ANA = os.path.join(WK, "analysis"); FR = os.path.join(ANA, "frames")
VIS = os.path.join(WK, "vision", "per_clip.json")
TARGET = 180.0
SEC_MAP = {"起步": 0, "林间": 1, "爬升": 2, "开阔": 3, "登顶": 4}
MINL = 2.0
DROP = {"C1827S03.mp4", "C1905S03.mp4", "C1906S03.mp4", "C1907S03.mp4", "C1908S03.mp4", "C1909S03.mp4"}

pc = json.load(open(os.path.join(ANA, "per_clip.json"), encoding="utf-8-sig"))
vp = {r["file"]: r for r in json.load(open(VIS, encoding="utf-8-sig"))}

def blocked_iv(f):
    r = vp.get(f) or {}
    out = []
    for iv in (r.get("blocked_ranges") or []):
        try: out.append((float(iv[0]), float(iv[1])))
        except Exception: pass
    return out

def chunk_ok(a, b, blocked):
    """Return longest sub-window of [a,b] that avoids blocked intervals."""
    cur = [(a, b)]
    for (x, y) in blocked:
        nxt = []
        for (p, q) in cur:
            if y <= p or x >= q: nxt.append((p, q)); continue
            if x > p: nxt.append((p, min(x, q)))
            if y < q: nxt.append((max(y, p), q))
        cur = nxt
    cur = [(p, q) for (p, q) in cur if q - p >= MINL]
    return max(cur, key=lambda t: t[1] - t[0]) if cur else None

rows = []
for f in sorted(pc.keys()):
    if f in DROP: continue
    c = pc[f]; keep = c.get("keep") or []
    if not keep: continue
    grade = c.get("grade") or "C"
    v = vp.get(f) or {}
    if float(v.get("mean_p_blocked") or 0) >= 0.55:
        print("  drop blocked-heavy %s (p_blocked %.2f)" % (f, v.get("mean_p_blocked")))
        continue
    bl = blocked_iv(f)
    best = None
    for kv in keep:
        a, b = float(kv[0]), float(kv[1])
        sub = chunk_ok(a, b, bl)
        if sub and (best is None or sub[1] - sub[0] > best[1] - best[0]):
            best = sub
    if best is None: continue
    rows.append(dict(file=f, a=best[0], b=best[1], grade=grade, q=float(c.get("q") or 0),
                     luma=float(c.get("mean_luma") or 120),
                     sec=SEC_MAP.get(c.get("section"), 2), vista=float(v.get("mean_p_wide_vista") or 0)))
print("clips kept: %d" % len(rows))

shots = []
for c in rows:
    avail = c["b"] - c["a"]
    want = {"A": min(6.0, avail), "B": min(5.0, avail), "C": min(3.0, avail)}.get(c["grade"], 3.0)
    ln = max(MINL, min(avail, want, 6.0))
    s0 = c["a"] + max(0.0, (avail - ln) * 0.5)
    shots.append(dict(file=c["file"], start=round(min(s0, c["b"] - ln), 2), dur=round(ln, 2),
                      sec=c["sec"], grade=c["grade"], q=c["q"], luma=c["luma"], avail=round(avail, 2)))
shots.sort(key=lambda s: s["file"])
print("initial total %.1f s over %d shots" % (sum(s["dur"] for s in shots), len(shots)))

# ---- trim to target (transitions recomputed afterwards) ----
def trans_over(s):
    ov = 0.0
    for i in range(len(s) - 1):
        if s[i]["sec"] != s[i + 1]["sec"]: ov += 0.7
    return ov
need = TARGET + trans_over(shots)
while sum(s["dur"] for s in shots) > need + 0.5:
    cg = [i for i in range(len(shots)) if shots[i]["grade"] == "C"]
    mid = [i for i in cg if shots[i]["sec"] not in (0, 4)]
    if mid:
        shots.pop(min(mid, key=lambda j: shots[j]["q"])); continue
    if cg and sum(s["dur"] for s in shots) > need + 12:
        shots.pop(min(cg, key=lambda j: shots[j]["q"])); continue
    cand = [i for i in range(len(shots)) if shots[i]["dur"] > MINL + 0.01]
    if not cand: break
    i = max(cand, key=lambda j: shots[j]["dur"])
    shots[i]["dur"] = max(MINL, round(shots[i]["dur"] - 0.5, 2))
while sum(s["dur"] for s in shots) < need - 0.5:
    cand = [i for i in range(len(shots)) if shots[i]["dur"] + 0.5 <= min(6.0, shots[i]["avail"])]
    if not cand: break
    i = max(cand, key=lambda j: shots[j]["q"])
    shots[i]["dur"] = round(shots[i]["dur"] + 0.5, 2)

# ---- transitions AFTER final list ----
tv = [0.0] * len(shots); tty = [""] * len(shots)
for i in range(len(shots) - 1):
    if shots[i]["sec"] != shots[i + 1]["sec"]:
        tv[i] = 0.7; tty[i] = "fade"
strong = [i for i in range(len(shots) - 1) if tv[i] == 0]
strong.sort(key=lambda i: -shots[i]["q"])
for i in strong[:7]:
    tv[i] = 0.45
    tv[i] = 0.45
    tty[i] = "circleopen" if shots[i + 1]["sec"] == 4 else ("smoothleft" if i % 3 == 0 else "dissolve")
tover = sum(tv[:-1])
print("transitions: %d (overlap %.2fs)" % (sum(1 for t in tv if t > 0), tover))

def levels(f, t0, t1):
    d = os.path.join(FR, f.replace(".mp4", ""))
    if not os.path.isdir(d): return None
    ys = []
    for i in range(int(round(t0 * 2)) - 1, int(round(t1 * 2)) + 2):
        for name in ("sec_%04d.jpg" % (i + 1), "sec_%04d.jpg" % (i + 2)):
            p = os.path.join(d, name)
            if os.path.exists(p):
                a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
                ys.append(0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]); break
    if not ys: return None
    Y = np.concatenate([y.ravel() for y in ys])
    L = max(0.02, min(0.95, float(Y.mean()) / 255.0))
    import math
    target = 0.42
    g = math.log(L) / math.log(target)
    g = max(0.80, min(1.95, g))
    b = max(-0.03, min(0.06, (target - L) * 0.10))
    return "eq=gamma=%.3f:brightness=%.4f" % (g, b)

edl = {"shots": []}
for i, s in enumerate(shots):
    edl["shots"].append(dict(file=s["file"], start=s["start"], dur=s["dur"], speed=1.0,
                             trans=round(tv[i], 2), trans_type=tty[i], sec=s["sec"],
                             grade=s["grade"], eqs=levels(s["file"], s["start"], s["start"] + s["dur"])))
json.dump(edl, open(os.path.join(WK, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
tot = sum(s["dur"] for s in shots) - sum(tv[:-1])
print("TOTAL %.2f  shots %d" % (tot, len(shots)))
print("sections:", dict(Counter(s["sec"] for s in shots)), "grades:", dict(Counter(s["grade"] for s in shots)))
