# -*- coding: utf-8 -*-
import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(OUT,"meta.json"), encoding="utf-8"))

mask = {}
stat = {"high":0, "mid":0, "mid-lowtex":0}
secs = {"high":0, "mid":0, "mid-lowtex":0}
for fn in sorted(M):
    runs = []
    for b in S[fn]["blocked"]:
        if b["conf"] not in ("high","mid"): continue
        if b["label"] not in ("BLUR","BLOCK","BLACK","WHITE"): continue
        sev = b["conf"]
        if b["label"] == "BLUR" and b["median_sharp"] > 250:
            sev = "mid-lowtex"
        runs.append([b["start"], b["end"]+1, sev, b["median_sharp"], b["median_fineratio"]])
        stat[sev] += 1
        secs[sev] += b["dur"]
    runs.sort()
    mask[fn] = {"dur": meta[fn]["n_frames"], "runs": runs}
tmp = os.path.join(OUT, "mask.json.tmp")
with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(mask, fh, ensure_ascii=False, separators=(",", ":"))
os.replace(tmp, os.path.join(OUT, "mask.json"))

tot_runs = sum(len(v["runs"]) for v in mask.values())
tot_sec = sum(e-s for v in mask.values() for s,e,sev,a,bb in v["runs"])
print("files:", len(mask), " total runs:", tot_runs, " total mask seconds:", tot_sec)
print("runs by severity:", stat)
print("seconds by severity:", secs)
print("files with empty runs:", [fn for fn in mask if not mask[fn]["runs"]])
print("raw bytes:", os.path.getsize(os.path.join(OUT,"mask.json")))
print()
for fn in sorted(mask):
    if mask[fn]["runs"]:
        print("  %-16s %s" % (fn, " ".join("%d-%d:%s" % (a,b,c) for a,b,c,d,e in mask[fn]["runs"])))
# BOM check
b = open(os.path.join(OUT,"mask.json"),"rb").read(4)
print()
print("first 4 bytes:", b, "BOM:", b[:3] == b"\xef\xbb\xbf")

# which seconds of the CLEAN batch would a sharp>=300 gate reject?
print()
print("=== clean-batch seconds rejected by sharp < 300 (gate alone) ===")
clean=[fn for fn in sorted(S) if S[fn]["usable_ratio"]>=0.98]
for fn in clean:
    bad=[f["t"] for f in M[fn] if f["sharp"]<300]
    if bad: print("  %-16s %d s: %s" % (fn, len(bad), bad))
print()
print("=== also check: does any of them look like sky/water (uniform/lumastd)? ===")
for fn in clean:
    for f in M[fn]:
        if f["sharp"]<300:
            print("  %s t=%d sharp=%.0f fineratio=%.3f uni=%.2f lumastd=%.1f luma=%.0f colored=%.0f" % (
                fn, f["t"], f["sharp"], f["fineratio"], f["uniform"], f["lumastd"], f["luma"], f["colorful"]))
