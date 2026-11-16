# -*- coding: utf-8 -*-
"""Cross-clip duplicate detection: dHash/aHash + HSV-histogram over 2fps frames."""
import os, sys, json, glob, math, itertools
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
HASHES = os.path.join(OUT, "hashes")

def hamming(a, b):
    return bin(a ^ b).count("1")

def cos(u, v):
    dot = sum(x*y for x, y in zip(u, v))
    nu = math.sqrt(sum(x*x for x in u)); nv = math.sqrt(sum(y*y for y in v))
    return dot / max(nu*nv, 1e-9)

def load():
    clips = {}
    for p in sorted(glob.glob(os.path.join(HASHES, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        clips[d["file"]] = d
    return dict(sorted(clips.items()))

def analyze_pair(A, B):
    fa, fb = A["frames"], B["frames"]
    if not fa or not fb:
        return None
    # per-frame match: strong = dhash<=8 and hist cos>=0.92
    pairs = []       # (ia, ib, dh, cos)
    for i, a in enumerate(fa):
        best = None
        for j, b in enumerate(fb):
            dh = hamming(a["dhash"], b["dhash"])
            if best is not None and dh >= best[2]:
                continue
            c = cos(a["hist"], b["hist"])
            if best is None or (dh + 12*(1-c)) < (best[2] + 12*(1-best[3])):
                best = (i, j, dh, c)
        if best is None:
            continue
        i, j, dh, c = best
        if dh <= 8 and c >= 0.92:
            pairs.append((i, j, dh, c))
    covA = len({p[0] for p in pairs}) / max(len(fa), 1)
    covB = len({p[1] for p in pairs}) / max(len(fb), 1)
    cover = min(covA, covB)
    if not pairs:
        return {"cover": 0.0, "covA": 0.0, "covB": 0.0, "n": 0, "med_dh": None, "med_cos": None,
                "mono": 0.0, "best": None}
    dhs = sorted(p[2] for p in pairs); css = sorted(p[3] for p in pairs)
    med_dh = dhs[len(dhs)//2]; med_cos = css[len(css)//2]
    # monotonic alignment of matched indices (same direction through time)
    seq = sorted(pairs, key=lambda p: p[0])
    inc = sum(1 for k in range(1, len(seq)) if seq[k][1] >= seq[k-1][1])
    mono = inc / max(len(seq)-1, 1) if len(seq) > 1 else 1.0
    bsrc = min(pairs, key=lambda p: p[2])
    return {"cover": round(cover, 3), "covA": round(covA, 3), "covB": round(covB, 3), "n": len(pairs),
            "med_dh": med_dh, "med_cos": round(med_cos, 4), "mono": round(mono, 3),
            "best": {"ia": bsrc[0], "ib": bsrc[1], "tA": fa[bsrc[0]]["t"], "tB": fb[bsrc[1]]["t"],
                     "dh": bsrc[2], "cos": round(bsrc[3], 4)}}

def main():
    clips = load()
    names = list(clips.keys())
    print("clips:", len(names), " frames total:", sum(len(c["frames"]) for c in clips.values()))
    out = []
    related = []
    for A, B in itertools.combinations(names, 2):
        r = analyze_pair(clips[A], clips[B])
        if r is None or r["cover"] <= 0:
            continue
        rec = {"A": A, "B": B, "cover": r["cover"], "covA": r["covA"], "covB": r["covB"],
               "n_match_frames": r["n"], "median_dhash": r["med_dh"], "median_hist_cos": r["med_cos"],
               "monotonic": r["mono"], "best": r["best"]}
        if r["cover"] >= 0.6 and r["med_dh"] is not None and r["med_dh"] <= 6 and r["med_cos"] >= 0.95:
            rec["verdict"] = "duplicate"
        elif r["cover"] >= 0.4 and r["med_dh"] is not None and r["med_dh"] <= 10:
            rec["verdict"] = "likely-dup"
        elif r["cover"] >= 0.25:
            rec["verdict"] = "related"
        elif r["n"] >= 2:
            rec["verdict"] = "touch"     # only a couple of frames overlap = passing the same spot
        else:
            continue
        (out if rec["verdict"] in ("duplicate", "likely-dup") else related).append(rec)
    out.sort(key=lambda r: -(r["cover"]))
    related.sort(key=lambda r: -(r["cover"]))
    json.dump(out, open(os.path.join(OUT, "dupes_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(related, open(os.path.join(OUT, "dupes_related.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()
    print("=== DUPLICATE / LIKELY-DUP pairs ===")
    for r in out:
        print("%-14s <-> %-14s cover=%.2f (A%.2f/B%.2f) n=%2d medDH=%s cos=%s mono=%.2f %s" % (
            r["A"], r["B"], r["cover"], r["covA"], r["covB"], r["n_match_frames"],
            r["median_dhash"], r["median_hist_cos"], r["monotonic"], r["verdict"]))
    print()
    print("=== related (same scene, weaker) === top 15")
    for r in related[:15]:
        print("%-14s <-> %-14s cover=%.2f n=%2d medDH=%s cos=%s mono=%.2f %s" % (
            r["A"], r["B"], r["cover"], r["n_match_frames"], r["median_dhash"], r["median_hist_cos"], r["monotonic"], r["verdict"]))
    print()
    print("related/touch pairs total:", len(related))

if __name__ == "__main__":
    main()
