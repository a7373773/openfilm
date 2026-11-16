# -*- coding: utf-8 -*-
"""mask.json: 遮挡/糊 区间（2fps 采样），阈值绝对+相对结合。"""
import os, json, math
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
M = json.load(open(os.path.join(OUT, "metrics.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8"))

def pct(a, p):
    s = sorted(a); k = (len(s)-1)*p; f = int(math.floor(k)); c = min(f+1, len(s)-1)
    return s[f] + (s[c]-s[f])*(k-f)

LBL = {"BLACK": "极暗/遮挡", "WHITE": "过曝白场", "BLOCK": "无细节/疑似遮挡",
       "BLUR": "低锐度/糊", "FLATS": "单色平板/天空"}
PRIO = ["BLACK", "WHITE", "BLOCK", "BLUR", "FLATS"]

def classify(fn):
    fr = M[fn]; n = len(fr)
    sh = [f["sharp"] for f in fr]
    ed = [f["edgefrac"] for f in fr]
    PS = max(pct(sh, 0.90), 1.0); PE = max(pct(ed, 0.90), 0.01)
    lab = [None]*n
    for i, f in enumerate(fr):
        d = f["sharp"]/PS; e = f["edgefrac"]/PE
        if (f["luma"] < 35 and f["edgefrac"] < 0.45) or (d < 0.12 and f["edgefrac"] < 0.18):
            lab[i] = "BLACK"
        elif f["luma"] > 235 or f["brightfrac"] > 0.80:
            lab[i] = "WHITE"
        elif f["edgefrac"] < 0.20 and f["sharp"] < 350:
            lab[i] = "BLOCK"
        elif d < 0.30 and f["fineratio"] < 0.105 and f["edgefrac"] < 0.55*PE:
            lab[i] = "BLUR"
        elif f["uniform"] > 0.55 and f["edgefrac"] < 0.45*PE:
            lab[i] = "FLATS"
    runs = []
    i = 0
    while i < n:
        if lab[i]:
            j = i
            while j+1 < n and lab[j+1]:
                j += 1
            runs.append([i, j]); i = j+1
        else:
            i += 1
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] <= 2:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    out = []
    for a, b in merged:
        k = b-a+1
        cnt = {}
        for t in range(a, b+1):
            if lab[t]: cnt[lab[t]] = cnt.get(lab[t], 0)+1
        main = max(cnt, key=lambda z: (cnt[z], -PRIO.index(z)))
        if main == "FLATS":
            continue
        msh = float(np.median([fr[t]["sharp"] for t in range(a, b+1)]))
        mfr = float(np.median([fr[t]["fineratio"] for t in range(a, b+1)]))
        t0 = round(a*0.5, 2); t1 = round((b+1)*0.5, 2)
        dur = t1-t0
        if dur < 1.0:
            sev = "low"
        elif dur < 2.0:
            sev = "mid"
        else:
            sev = "high"
        if main == "BLUR" and msh > 250 and sev != "low":
            sev = "mid-lowtex"
        out.append({"start": t0, "end": t1, "dur": round(dur,2), "label": main, "sev": sev,
                    "sharp": round(msh,1), "fineratio": round(mfr,3),
                    "mean_luma": round(float(np.mean([fr[t]["luma"] for t in range(a,b+1)])),1),
                    "mean_edge": round(float(np.mean([fr[t]["edgefrac"] for t in range(a,b+1)])),3),
                    "mean_uniform": round(float(np.mean([fr[t]["uniform"] for t in range(a,b+1)])),3),
                    "mean_diff": round(float(np.mean([fr[t]["diff"] for t in range(a,b+1)])),1)})
    return out, PS, PE

def main():
    mask = {}; flats = {}
    stats = {}
    for fn in sorted(M):
        runs, PS, PE = classify(fn)
        kept = [r for r in runs if r["sev"] != "low"]
        mask[fn] = {"dur": meta[fn]["n_frames"]*0.5, "runs": [[r["start"], r["end"], r["sev"], r["sharp"], r["fineratio"]] for r in kept]}
        flats[fn] = [ [r["start"], r["end"], r["sharp"], r["fineratio"], r["mean_uniform"]] for r in runs if r["label"]=="FLATS"]
        stats[fn] = {"P90_sharp": round(PS,1), "P90_edge": round(PE,3),
                     "runs_all": runs, "flagged_sec": round(sum(r["dur"] for r in runs),2)}
    json.dump(mask, open(os.path.join(OUT, "mask.json"), "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=0)
    json.dump(stats, open(os.path.join(OUT, "mask_detail.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(flats, open(os.path.join(OUT, "flats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tots = sum(meta[fn]["n_frames"]*0.5 for fn in M)
    flagged = sum(stats[fn]["flagged_sec"] for fn in M)
    print("files:", len(mask), " total %.2fs  flagged %.2fs (%.1f%%)" % (tots, flagged, 100*flagged/tots))
    from collections import Counter
    c = Counter()
    for fn in mask:
        for r in mask[fn]["runs"]:
            c[r[2]] += r[1]-r[0]
    print("seconds by severity:", dict(c))
    print("empty mask files:", sum(1 for fn in mask if not mask[fn]["runs"]))
    print()
    for fn in sorted(mask):
        if mask[fn]["runs"]:
            print("%-14s %s" % (fn, " ".join("%.1f-%.1f:%s(s%.0f,f%.3f)" % (a,b,c2,d,e) for a,b,c2,d,e in mask[fn]["runs"])))
    print()
    print("=== fully-flagged (literally unusable) clips ===")
    for fn in sorted(M):
        if stats[fn]["flagged_sec"] >= meta[fn]["n_frames"]*0.5 - 0.01:
            print("  %-14s dur=%.2f all flagged" % (fn, meta[fn]["n_frames"]*0.5))
    print()
    print("=== FLATS (天空/平板, 不进 mask) ===")
    for fn in sorted(flats):
        if flats[fn]: print("  %-14s %s" % (fn, flats[fn]))

if __name__ == "__main__":
    main()
