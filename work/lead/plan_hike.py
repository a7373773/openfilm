# -*- coding: utf-8 -*-
"""Build the ordered 3-minute hiking EDL (v3: relaxed gates, proper duration allocator)."""
import json, os, math
import numpy as np

WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
ANA = os.path.join(WK, "analysis"); TAGS = os.path.join(WK, "vision", "tags.json")
OUT = os.path.join(WK, "edl.json")
TARGET = 180.0
SEC_NAMES = ["出发", "林间", "爬升", "陡坡", "山脊", "登顶"]
MINL, MAXL, STEP = 2.0, 6.0, 0.5

def main():
    m = json.load(open(os.path.join(ANA, "metrics.json"), encoding="utf-8-sig"))
    tags = json.load(open(TAGS, encoding="utf-8-sig")) if os.path.exists(TAGS) else {}
    dup = json.load(open(os.path.join(ANA, "dupes_raw.json"), encoding="utf-8-sig")) \
          if os.path.exists(os.path.join(ANA, "dupes_raw.json")) else []
    files = sorted(m.keys()); n = len(files)

    drop = set()
    for d in dup:
        if d.get("cover", 0) >= 0.35:
            a, b = d["A"], d["B"]
            sa = np.mean([x["sharp"] for x in m[a]]); sb = np.mean([x["sharp"] for x in m[b]])
            drop.add(a if sa < sb else b)
    print("dupes dropped:", sorted(drop))

    clips = {}
    for f in files:
        if f in drop: continue
        rows = m[f]
        # exclude clips that are both soft and dim (measured: these look mushy on screen)
        mean_sharp = float(np.mean([x["sharp"] for x in rows]))
        mean_luma = float(np.mean([x["luma"] for x in rows]))
        if mean_sharp < 250 and mean_luma < 160:
            print("  exclude soft/dim clip %s (sharp %.0f luma %.0f)" % (f, mean_sharp, mean_luma))
            continue
        tm = {round(float(r["t"]), 1): r for r in tags.get(f, [])}
        sh = np.array([x["sharp"] for x in rows]); floor = max(100.0, 0.28 * float(np.median(sh)))
        fr = []
        for x in rows:
            tr = tm.get(round(float(x["t"]), 1), {})
            pp = tr.get("p_person", .5); pb = tr.get("p_blocked", .0); pbl = tr.get("p_blurry", .5)
            pc = tr.get("p_clear", .4); pv = tr.get("p_wide_vista", .0); pback = tr.get("p_back", .0)
            ok = (x["sharp"] >= floor and x["entropy"] >= 3.9 and 35 <= x["luma"] <= 225 and pb <= 0.55)
            q = min(1.5, (x["sharp"] / max(floor, 1)) ** 0.30)
            q *= 0.72 + 0.28 * min(1.5, x["colorful"] / 32.0)
            q *= 0.82 + 0.18 * pc
            q *= 0.85 + 0.30 * pp
            q *= 1.0 + 0.60 * pv + 0.20 * pback
            q *= (1.0 - 0.40 * pb) * (1.0 - 0.25 * pbl)
            if x["diff"] > 45: q *= 0.85
            fr.append(dict(t=round(float(x["t"]), 1), ok=bool(ok), q=float(q), pp=float(pp),
                           pv=float(pv), pback=float(pback), diff=float(x["diff"]),
                           sharp=float(x["sharp"]), pb=float(pb), pbl=float(pbl)))
        wins = {}
        dur = fr[-1]["t"] + 0.5
        for L in [x * STEP for x in range(int(MINL / STEP), int(min(MAXL, dur - 0.05) / STEP) + 1)]:
            nl = int(round(L / STEP)); best = None
            for s in range(0, len(fr) - nl + 1):
                seg = fr[s:s + nl]
                if not all(r["ok"] for r in seg): continue
                sc = float(np.mean([r["q"] for r in seg]))
                v = sc * 0.72 + float(np.min([r["q"] for r in seg])) * 0.28
                if best is None or v > best[0]:
                    best = (v, seg[0]["t"], sc, seg)
            if best:
                wins[L] = dict(v=best[0], start=best[1], sc=best[2],
                               pp=float(np.mean([r["pp"] for r in best[3]])),
                               pv=float(np.mean([r["pv"] for r in best[3]])),
                               pback=float(np.mean([r["pback"] for r in best[3]])),
                               diff=float(np.mean([r["diff"] for r in best[3]])))
        if not wins: continue
        clips[f] = dict(wins=wins, Lmax=max(wins), v=max(w["v"] for w in wins.values()), dur=dur, order=int(f[1:5]))
    print("usable clips: %d / %d" % (len(clips), n))
    if not clips: raise SystemExit("no usable clips")

    # narrative section by rank among usable clips (not raw index)
    ranked = sorted(clips.keys(), key=lambda f: clips[f]["order"])
    for i, f in enumerate(ranked):
        clips[f]["sec"] = min(len(SEC_NAMES) - 1, int(i / len(ranked) * len(SEC_NAMES)))

    picked = []
    for si in range(len(SEC_NAMES)):
        ss = [c for c in clips.values() if c["sec"] == si]
        if si == 0:      # opener must be able to hold 4.5s for the title card
            ss.sort(key=lambda c: (c["Lmax"] < 4.5, -c["v"]))
        elif si == len(SEC_NAMES) - 1:   # finale must hold long (end card)
            ss.sort(key=lambda c: (c["Lmax"] < 5.0, -max((w["pv"] for L, w in c["wins"].items() if L >= 4.5), default=0)))
        else:
            ss.sort(key=lambda c: -c["v"])
        picked += ss
    picked.sort(key=lambda c: c["order"])
    print("shots picked: %d" % len(picked))
    for si in range(len(SEC_NAMES)):
        print("  %s: %d" % (SEC_NAMES[si], sum(1 for c in picked if c["sec"] == si)))

    # transitions: section changes + a few dissolves
    def base_trans(i):
        if i + 1 >= len(picked): return 0.0, ""
        if picked[i]["sec"] != picked[i + 1]["sec"]: return 0.7, "fade"
        return 0.0, ""
    cand = [i for i in range(len(picked) - 1) if base_trans(i)[0] == 0.0]
    cand.sort(key=lambda i: -picked[i]["v"])
    for i in cand[:7]:
        picked[i]["_dis"] = 0.45

    def trans(i):
        if i + 1 >= len(picked): return 0.0, ""
        t, ty = base_trans(i)
        if t: return t, ty
        if picked[i].get("_dis"):
            nxt = picked[i + 1]
            ty = "circleopen" if nxt["sec"] == len(SEC_NAMES) - 1 else ("smoothleft" if i % 3 == 0 else "dissolve")
            return 0.45, ty
        return 0.0, ""
    trs = [trans(i) for i in range(len(picked))]
    tover = sum(t for t, _ in trs[:-1])

    # ---- duration allocator ----
    durs = [min(max(2.5, 0.75 * c["Lmax"]), MAXL) for c in picked]
    durs = [round(min(d, c["Lmax"]) * 2) / 2.0 for d, c in zip(durs, picked)]
    # minimums: let the title card and the end card breathe
    MIN_SPECIAL = {0: 4.5, 1: 3.5, 2: 3.0, len(picked) - 1: 5.0, len(picked) - 2: 4.0}
    for i, m_ in MIN_SPECIAL.items():
        if 0 <= i < len(durs):
            durs[i] = max(durs[i], min(m_, picked[i]["Lmax"]))
    budget = TARGET + tover
    for _ in range(400):
        tot = sum(durs)
        delta = budget - tot
        if abs(delta) < 0.25: break
        if delta > 0:                       # grow: give to shots with headroom, weighted by quality
            room = [max(0.0, c["Lmax"] - d) for c, d in zip(picked, durs)]
            if sum(room) < 0.5: break
            w = np.array([max(1e-6, r) * (0.5 + c["v"]) for r, c in zip(room, picked)])
            w /= w.sum()
            durs = [d + min(r, delta * wi) for d, r, wi in zip(durs, room, w)]
        else:
            room = [max(0.0, d - MINL) for d in durs]
            if sum(room) < 0.5: break
            w = np.array([max(1e-6, r) for r in room]); w /= w.sum()
            durs = [d - min(r, -delta * wi) for d, r, wi in zip(durs, room, w)]
        durs = [round(d * 2) / 2.0 for d in durs]
    total = sum(durs) - tover
    print("total=%.2f (target %.1f)  shots=%d  trans=%d" % (
        total, TARGET, len(picked), sum(1 for t, _ in trs[:-1] if t > 0)))

    shots = []
    for i, c in enumerate(picked):
        d = durs[i]
        L = d
        while L not in c["wins"] and L > MINL:
            L = round(L - STEP, 2)
        if L not in c["wins"]:
            L = min(c["wins"])
        w = c["wins"][L]
        shots.append(dict(file=None, start=round(w["start"], 2), dur=L, speed=1.0,
                          trans=round(trs[i][0], 2), trans_type=trs[i][1], sec=c["sec"],
                          v=round(c["v"], 3), pv=round(w["pv"], 3), pback=round(w["pback"], 3),
                          pp=round(w["pp"], 3)))
    fname = {id(c): f for f, c in clips.items()}
    for i, c in enumerate(picked):
        shots[i]["file"] = fname[id(c)]
    total = sum(s["dur"] for s in shots) - sum(s["trans"] for s in shots[:-1])
    json.dump(dict(shots=shots), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("FINAL total=%.2f shots=%d" % (total, len(shots)))
    for i, s in enumerate(shots):
        print("%2d %-14s in=%5.2f dur=%4.2f tr=%.2f %-10s sec=%d pv=%.2f pp=%.2f" % (
            i, s["file"], s["start"], s["dur"], s["trans"], s["trans_type"], s["sec"], s["pv"], s["pp"]))

if __name__ == "__main__":
    main()
