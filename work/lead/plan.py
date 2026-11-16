# -*- coding: utf-8 -*-
"""Build an EDL from per-second metrics + CLIP tags.

Selection rule: a shot is only used if EVERY source second inside it passes hard
quality gates (sharpness floor, exposure, not-flat, CLIP landscape score). Among the
valid windows we pick the highest scoring ones with file/scene diversity.
"""
import json, os, sys, math
import numpy as np
from PIL import Image

W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work"
ANA = os.path.join(W, "analysis")
FRAMES = os.path.join(ANA, "frames")
TAGS = os.path.join(W, "vision", "tags.json")
XSECS = 0.5
FPS = 30

# on-screen durations in seconds: multiples of 1.25 s = 2 beats @ 96 bpm (bar = 2.5 s)
RHYTHM = [6.0, 3.75, 3.75, 3.75, 2.5, 3.75, 3.75, 2.5, 3.75, 3.75, 3.75, 2.5,
          3.75, 3.75, 3.75, 2.5, 3.75, 5.0]
TARGET_TOTAL = 57.5
SLOW_SLOTS = {2, 5, 8, 12, 16}   # which shots get 0.5x slow motion
CLIP_MIN_LANDSCAPE = 0.42
CLIP_MAX_BLOCKED = 0.45
CLIP_MIN_PCT = 0.58
SCENE_FEAT = os.path.join(ANA, "scene_feat.json")
# Only files that BOTH analyses agree are predominantly clean landscape:
#  - pixel side: analyst mask + sharpness floor, few/no masked seconds
#  - CLIP side: p_landscape high, p_closeup/hand/fabric low
# Excluded on purpose: REC-0023..0027 (CLIP: ground/close-up), REC-0019 (same),
# REC-0001..0006 (soft batch / occlusion), REC-0002 (hand+fabric).
ALLOWED = {"REC-0007-A.mp4", "REC-0012-A.mp4", "REC-0013-A.mp4", "REC-0014-A.mp4",
           "REC-0015-A.mp4", "REC-0016-A.mp4", "REC-0017-A.mp4", "REC-0018-A.mp4",
           "REC-0020-A.mp4", "REC-0021-A.mp4", "REC-0022-A.mp4"}


def load():
    m = json.load(open(os.path.join(ANA, "metrics.json"), encoding="utf-8-sig"))
    tags = {}
    if os.path.exists(TAGS):
        tags = json.load(open(TAGS, encoding="utf-8-sig"))
    mask = {}
    mp = os.path.join(ANA, "mask.json")
    if os.path.exists(mp):
        mask = json.load(open(mp, encoding="utf-8-sig"))
    return m, tags, mask


def masked_seconds(mask, f):
    out = set()
    ent = mask.get(f) or {}
    runs = ent.get("runs") if isinstance(ent, dict) else ent
    for r in (runs or []):
        try:
            a, b = int(r[0]), int(r[1])
        except Exception:
            continue
        for t in range(a, b):
            out.add(t)
    return out


def build(m, tags, mask):
    files = {}
    global_land = []
    sf = {}
    if os.path.exists(SCENE_FEAT):
        sf = json.load(open(SCENE_FEAT, encoding="utf-8-sig"))
    for f, fr in m.items():
        masked = masked_seconds(mask, f)
        nat = {}
        for rec in sf.get(f.replace(".mp4", ""), []):
            nat[int(rec["t"])] = min(1.5, rec.get("sky", 0) + rec.get("veg", 0) + rec.get("water", 0))
        n = len(fr)
        sh = np.array([x["sharp"] for x in fr], float)
        lu = np.array([x["luma"] for x in fr], float)
        un = np.array([x["uniform"] for x in fr], float)
        en = np.array([x["entropy"] for x in fr], float)
        dk = np.array([x["darkfrac"] for x in fr], float)
        cf = np.array([x["colorful"] for x in fr], float)
        df = np.array([x["diff"] for x in fr], float)
        med = float(np.median(sh))
        p60 = float(np.percentile(sh, 60))
        floor = 300.0   # analyst-recommended absolute sharpness floor (file-relative P90 handled by mask)
        tagmap = {}
        for rec in tags.get(f, []):
            t = int(rec.get("t", 0))
            # tags t is 1-based over frames; metrics t is 0-based seconds
            tagmap.setdefault(t - 1, rec)
            tagmap.setdefault(t, rec)
        rows = []
        for i in range(n):
            tr = tagmap.get(i, {})
            pl = tr.get("p_landscape")
            pb = tr.get("p_blocked")
            pp = tr.get("p_landscape_pct")
            if pl is not None: global_land.append(float(pl))
            ok, why = True, []
            if i in masked: ok = False; why.append("masked")
            if sh[i] < floor: ok = False; why.append("soft")
            if lu[i] < 55 or lu[i] > 218: ok = False; why.append("expo")
            if dk[i] > 0.5: ok = False; why.append("dark")
            if en[i] < 4.2: ok = False; why.append("flat")
            if pl is not None and float(pl) < CLIP_MIN_LANDSCAPE: ok = False; why.append("npland")
            if pb is not None and float(pb) > CLIP_MAX_BLOCKED: ok = False; why.append("blocked")
            if pp is not None and float(pp) < CLIP_MIN_PCT: ok = False; why.append("lowpct")
            if pl is None: ok = False; why.append("notag")
            q = 1.0
            q *= min(1.5, (sh[i] / max(floor, 1.0)) ** 0.35)
            q *= 0.8 + 0.2 * min(1.6, cf[i] / 32.0)
            q *= 1.0 - 0.35 * abs(lu[i] - 128.0) / 128.0
            if df[i] > 75: q *= 0.8
            if pl is not None: q *= 0.60 + 0.40 * float(pl)
            if pp is not None: q *= 0.85 + 0.15 * min(1.0, float(pp))
            if i in nat: q *= 0.85 + 0.15 * min(1.0, nat[i])
            rows.append(dict(t=i, ok=ok, why=why, score=q, sharp=sh[i], luma=lu[i],
                             nat=nat.get(i, 0.0),
                             diff=df[i], colorful=cf[i],
                             p_landscape=(float(pl) if pl is not None else None),
                             p_pct=(float(pp) if pp is not None else None),
                             p_blocked=(float(pb) if pb is not None else None),
                             scene=tr.get("scene")))
        credit = sum(1 for r in rows if r["ok"])
        files[f] = dict(rows=rows, median=med, floor=floor, credit=credit)
    return files, (float(np.percentile(global_land, 50)) if global_land else None)


def windows(files, need_sec):
    """All fully-valid integer-start windows of length need_sec, per file."""
    out = []
    for f, info in files.items():
        if f not in ALLOWED:                 # file-level whitelist (see ALLOWED)
            continue
        if info.get("credit", 0) < 15:      # too few trustworthy seconds -> unreliable file
            continue
        rows = info["rows"]
        n = len(rows)
        L = int(math.ceil(need_sec))
        for s in range(0, n - L + 1):
            seg = rows[s:s + L]
            if not all(r["ok"] for r in seg):
                continue
            sc = [r["score"] for r in seg]
            pls = [r["p_landscape"] for r in seg if r["p_landscape"] is not None]
            out.append(dict(file=f, start=s, need=need_sec, L=L,
                            mean=float(np.mean(sc)), mins=float(np.min(sc)),
                            mean_diff=float(np.mean([r["diff"] for r in seg])),
                            mean_sharp=float(np.mean([r["sharp"] for r in seg])),
                            scene=seg[L // 2]["scene"],
                            nat=float(np.mean([r.get("nat", 0.0) for r in seg])),
                            pl=float(np.mean(pls)) if pls else None,
                            pct=float(np.mean([r["p_pct"] for r in seg if r.get("p_pct") is not None]))))
    out.sort(key=lambda r: -(r["mean"] * 0.6 + r["mins"] * 0.4))
    return out


def levels_for(f, t0, t1):
    d = os.path.join(FRAMES, f.replace(".mp4", ""))
    if not os.path.isdir(d):
        return None
    ys = []
    for t in range(int(math.floor(t0)), int(math.ceil(t1)) + 1):
        for cand in ("sec_%04d.jpg" % t, "sec_%04d.jpg" % (t + 1)):
            q = os.path.join(d, cand)
            if os.path.exists(q):
                a = np.asarray(Image.open(q).convert("RGB")).astype(np.float32)
                ys.append(0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
                break
    if not ys:
        return None
    Y = np.concatenate([y.ravel() for y in ys])
    lo = float(np.percentile(Y, 1.0)) / 255.0
    hi = float(np.percentile(Y, 99.0)) / 255.0
    if hi - lo < 0.3:
        hi = min(1.0, lo + 0.3)
    k = 0.55
    mn = min(round(lo * k, 4), 0.16)
    mx = max(round(1.0 - (1.0 - hi) * k, 4), 0.80)
    return [mn, mx, mn, mx, mn, mx]


def main():
    m, tags, mask = load()
    files, pl_med = build(m, tags, mask)
    n_shots = len(RHYTHM)
    rhythm = list(RHYTHM)
    raw = sum(rhythm) - XSECS * (n_shots - 1)
    rhythm[0] = round(rhythm[0] + (TARGET_TOTAL - raw), 3)
    print("CLIP tags: %s | global p_landscape median: %s" % (bool(tags), pl_med))
    print("shots: %d  total on-screen: %.2f s (opener %.2f s)" % (n_shots, sum(rhythm) - XSECS*(n_shots-1), rhythm[0]))

    # ---- fill slots by priority (opener & closer first) with timeline-aware constraints ----
    slots = [None] * n_shots
    per_file, used_spans = {}, {}
    WIN_CACHE = {}

    def get_windows(need):
        if need not in WIN_CACHE:
            WIN_CACHE[need] = windows(files, need)
        return WIN_CACHE[need]

    def overlaps(f, s, e, gap=2.0):
        for (a_, b_) in used_spans.get(f, []):
            if s < b_ + gap and e > a_ - gap:
                return True
        return False

    def neighbours(i):
        out = []
        for j in (i - 1, i + 1):
            if 0 <= j < n_shots and slots[j] is not None:
                out.append(slots[j])
        return out

    def score_candidate(c, i, allow_scene_rep):
        cap = 2 if per_file else 3
        if per_file.get(c["file"], 0) >= cap:
            return None
        if (c["start"], c["file"]) in used_spans.setdefault("_seen", set()):
            return None
        if overlaps(c["file"], c["start"], c["start"] + c["need"]):
            return None
        nbs = neighbours(i)
        for nb in nbs:
            if nb["file"] == c["file"]:
                return None
        adj = c["mean"] * 0.55 + c["mins"] * 0.45
        adj -= 0.10 * per_file.get(c["file"], 0)
        for nb in nbs:
            if c["scene"] and nb.get("scene") and c["scene"] == nb["scene"]:
                adj -= 0.05 if not allow_scene_rep else 0.0
        adj += 0.015 * min(1.0, c["mean_sharp"] / 3000.0)
        adj += 0.010 * min(1.0, files[c["file"]].get("credit", 0) / 60.0)
        if i == 0:
            adj += 0.04 * min(1.0, c.get("nat", 0) / 1.2)      # opener: open vista
        if i == n_shots - 1:
            adj += 0.04 * (1.0 - min(1.0, c["mean_diff"] / 60.0))  # closer: calm
            adj -= 0.05 * max(0.0, 0.45 - (c["pl"] if c["pl"] is not None else 0.45))
        return adj

    order = [0, n_shots - 1] + [i for i in range(1, n_shots - 1)]
    for i in order:
        dur = rhythm[i]
        speeds = [0.5, 1.0] if (i in SLOW_SLOTS and dur >= 3.75) else [1.0, 0.5]
        got, best_adj = None, -1e9
        for slow in speeds:                      # preferred speed first, all relax levels
            for relax in (0, 1, 2):
                need = dur * slow
                for c in get_windows(need):
                    adj = score_candidate(c, i, allow_scene_rep=(relax >= 2))
                    if adj is None:
                        continue
                    if relax >= 1:
                        adj -= 0.02          # mild penalty for relaxed pass
                    if adj > best_adj:
                        best_adj, got = adj, dict(c)
                        got["speed"] = slow
                        got["dur"] = dur
                if got is not None:
                    break
            if got is not None:
                break
        if got is None:
            raise SystemExit("cannot fill slot %d" % i)
        got["adj"] = round(best_adj, 3)
        slots[i] = got
        per_file[got["file"]] = per_file.get(got["file"], 0) + 1
        used_spans.setdefault(got["file"], []).append((got["start"], got["start"] + got["need"]))

    # ---- one improvement pass: re-pick any slot that can be upgraded ----
    for _ in range(2):
        changed = False
        for i in range(n_shots):
            cur = slots[i]
            dur = cur["dur"]
            saved = slots[i]
            slots[i] = None
            best, best_adj = None, cur["adj"]
            slow = cur["speed"]
            for c in get_windows(dur * slow):
                adj = score_candidate(c, i, allow_scene_rep=False)
                if adj is not None and adj > best_adj + 0.005:
                    best_adj, best = adj, dict(c)
                    best["speed"] = slow
                    best["dur"] = dur
                    best["adj"] = round(adj, 3)
            slots[i] = saved
            if best is not None:
                used_spans[saved["file"]].remove((saved["start"], saved["start"] + saved["need"]))
                per_file[saved["file"]] -= 1
                slots[i] = best
                per_file[best["file"]] = per_file.get(best["file"], 0) + 1
                used_spans.setdefault(best["file"], []).append((best["start"], best["start"] + best["need"]))
                changed = True
        if not changed:
            break
    chosen = slots

    shots = []
    for i, c in enumerate(chosen):
        src_len = c["dur"] * c["speed"]
        st = round(min(max(c["start"], 0), max(0, len(files[c["file"]]["rows"]) - src_len - 0.05)), 3)
        shots.append(dict(file=c["file"], start=st, dur=c["dur"], speed=c["speed"],
                          xfade=(XSECS if i < len(chosen) - 1 else 0.0),
                          transition="fade",
                          levels=levels_for(c["file"], st, st + src_len),
                          scene=c["scene"], p_landscape=(round(c["pl"], 3) if c["pl"] else None),
                          score=round(c["mean"], 3), mean_diff=round(c["mean_diff"], 1)))
    edl = dict(shots=shots)
    out = os.path.join(W, "lead", "edl.json")
    json.dump(edl, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot = sum(s["dur"] for s in shots) - XSECS * (len(shots) - 1)
    print("\nEDL ->", out, " total=%.2fs" % tot)
    for i, s in enumerate(shots):
        print("%2d %-16s t=%6.2f dur=%4.2f spd=%.1f scene=%-12s pl=%-5s sc=%.2f" % (
            i, s["file"], s["start"], s["dur"], s["speed"], str(s["scene"]),
            str(s["p_landscape"]), s["score"]))
    print("\nfiles used:", len(set(s["file"] for s in shots)))
    print("source consumed: %.1f s" % sum(s["dur"] * s["speed"] for s in shots))


if __name__ == "__main__":
    main()
