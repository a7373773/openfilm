# -*- coding: utf-8 -*-
"""Duplicate detection v2: numpy popcount matrices + structure guard + scene-similarity."""
import os, json, math, itertools
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
H = os.path.join(OUT, "hashes")
M = json.load(open(os.path.join(OUT, "metrics.json"), encoding="utf-8"))

def popcount(x):
    x = x - ((x >> np.uint64(1)) & np.uint64(0x5555555555555555))
    x = (x & np.uint64(0x3333333333333333)) + ((x >> np.uint64(2)) & np.uint64(0x3333333333333333))
    x = (x + (x >> np.uint64(4))) & np.uint64(0x0F0F0F0F0F0F0F0F)
    return (x * np.uint64(0x0101010101010101)) >> np.uint64(56)

def load():
    clips = {}
    for fn in sorted(os.listdir(H)):
        if not fn.endswith(".json"): continue
        d = json.load(open(os.path.join(H, fn), encoding="utf-8"))
        clips[d["file"]] = d
    return dict(sorted(clips.items()))

def matrices(A, B):
    da = np.array([f["dhash"] for f in A["frames"]], dtype=np.uint64)
    db = np.array([f["dhash"] for f in B["frames"]], dtype=np.uint64)
    DH = popcount(np.bitwise_xor(da[:, None], db[None, :])).astype(np.int16)
    ha = np.array([f["hist"] for f in A["frames"]], dtype=np.float64)
    hb = np.array([f["hist"] for f in B["frames"]], dtype=np.float64)
    ha /= np.maximum(np.linalg.norm(ha, axis=1, keepdims=True), 1e-9)
    hb /= np.maximum(np.linalg.norm(hb, axis=1, keepdims=True), 1e-9)
    COS = ha @ hb.T
    return DH, COS

def struct_ok(fn):
    fr = M[fn]
    e = float(np.mean([f["edgefrac"] for f in fr]))
    s = float(np.mean([f["sharp"] for f in fr]))
    return {"edge": e, "sharp": s, "structured": (e >= 0.22 and s >= 250)}

def pair_stats(A, B, T1=10, T2=0.90):
    DH, COS = matrices(A, B)
    m = (DH <= T1) & (COS >= T2)
    covA = m.any(axis=1).mean(); covB = m.any(axis=0).mean()
    cover = min(covA, covB)
    idx = np.argwhere(m)
    if len(idx) == 0:
        return {"cover": 0.0, "covA": 0.0, "covB": 0.0, "n": 0, "med_dh": None, "med_cos": None, "mono": 0.0, "best": None}
    dhs = DH[m]; css = COS[m]
    seq = idx[np.argsort(idx[:, 0])]
    inc = np.mean(seq[1:, 1] >= seq[:-1, 1]) if len(seq) > 1 else 1.0
    k = int(np.argmin(DH[m]))
    ia, ib = idx[k]
    return {"cover": round(float(cover), 3), "covA": round(float(covA), 3), "covB": round(float(covB), 3),
            "n": int(len(idx)), "med_dh": float(np.median(dhs)), "med_cos": round(float(np.median(css)), 4),
            "mono": round(float(inc), 3),
            "best": {"ia": int(ia), "ib": int(ib), "tA": A["frames"][int(ia)]["t"], "tB": B["frames"][int(ib)]["t"],
                     "dh": int(DH[ia, ib]), "cos": round(float(COS[ia, ib]), 4)}}

def main():
    clips = load(); names = list(clips.keys())
    info = {fn: struct_ok(fn) for fn in names}
    pairs = []; scene = []
    for A, B in itertools.combinations(names, 2):
        sa, sb = info[A], info[B]
        rs = pair_stats(clips[A], clips[B])
        scene_rec = None
        if rs["n"] > 0:
            dh, cos = rs["med_dh"], rs["med_cos"]
            ok = sa["structured"] and sb["structured"]
            rec = {"A": A, "B": B, "cover": rs["cover"], "covA": rs["covA"], "covB": rs["covB"],
                   "n_frames_matched": rs["n"], "median_dhash": dh, "median_hist_cos": rs["med_cos"],
                   "monotonic": rs["mono"], "best": rs["best"],
                   "A_structured": sa["structured"], "B_structured": sb["structured"]}
            if ok and rs["cover"] >= 0.5 and dh <= 8 and rs["med_cos"] >= 0.93:
                rec["verdict"] = "duplicate"
            elif ok and rs["cover"] >= 0.35 and dh <= 10:
                rec["verdict"] = "likely-dup"
            elif not ok and rs["cover"] >= 0.5 and rs["med_cos"] >= 0.95:
                rec["verdict"] = "blank-both"
            elif rs["cover"] >= 0.2:
                rec["verdict"] = "related"
            elif rs["n"] >= 2:
                rec["verdict"] = "touch"
            else:
                rec = None
            pairs.append(rec) if rec else None
        # scene similarity (clip-level colour + brightness)
        ha = np.mean([f["hist"] for f in clips[A]["frames"]], axis=0)
        hb = np.mean([f["hist"] for f in clips[B]["frames"]], axis=0)
        cos = float(ha @ hb / max(np.linalg.norm(ha)*np.linalg.norm(hb), 1e-9))
        la = float(np.mean([f["luma"] for f in M[A]])); lb = float(np.mean([f["luma"] for f in M[B]]))
        ska = float(np.mean([f["sky"] for f in clips[A]["frames"]])); skb = float(np.mean([f["sky"] for f in clips[B]["frames"]]))
        if cos >= 0.90 and abs(la-lb) <= 25:
            scene.append({"A": A, "B": B, "hist_cos": round(cos,4), "luma_diff": round(abs(la-lb),1),
                          "sky": [round(ska,3), round(skb,3)], "adjacent": abs(names.index(A)-names.index(B)) == 1})
    order = {"duplicate":0, "likely-dup":1, "blank-both":2, "related":3, "touch":4}
    pairs.sort(key=lambda r: (order[r["verdict"]], -r["cover"]))
    json.dump(pairs, open(os.path.join(OUT, "dupes_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(scene, open(os.path.join(OUT, "scene_similar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    print("pairs classified:", Counter(p["verdict"] for p in pairs))
    for r in pairs:
        print("%-13s %-13s %-12s cover=%.2f n=%3d medDH=%s medCOS=%s mono=%.2f struct=%s/%s" % (
            r["A"].replace("S03.mp4",""), r["B"].replace("S03.mp4",""), r["verdict"], r["cover"], r["n_frames_matched"],
            ("%.1f"%r["median_dhash"]) if r["median_dhash"] is not None else "-",
            r["median_hist_cos"], r["monotonic"], r["A_structured"], r["B_structured"]))
    print()
    print("scene-similar pairs:", len(scene))
    for s in scene:
        print("  %-13s %-13s cos=%.4f dLuma=%.0f sky=%.2f/%.2f adj=%s" % (
            s["A"].replace("S03.mp4",""), s["B"].replace("S03.mp4",""), s["hist_cos"], s["luma_diff"],
            s["sky"][0], s["sky"][1], s["adjacent"]))
    print()
    print("unstructured clips:", [fn.replace("S03.mp4","") for fn in names if not info[fn]["structured"]])

if __name__ == "__main__":
    main()
