# -*- coding: utf-8 -*-
import os, json
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
M=json.load(open(os.path.join(OUT,"metrics.json"),encoding="utf-8"))
meta=json.load(open(os.path.join(OUT,"meta.json"),encoding="utf-8"))
mask=json.load(open(os.path.join(OUT,"mask.json"),encoding="utf-8"))
pc=json.load(open(os.path.join(OUT,"per_clip.json"),encoding="utf-8"))
dp=json.load(open(os.path.join(OUT,"dupes.json"),encoding="utf-8"))
print("metrics keys:", len(M), " frames:", sum(len(v) for v in M.values()))
print("meta keys:", len(meta), " mask keys:", len(mask), " per_clip keys:", len(pc), " dupes entries:", len(dp))
print("BOM mask:", open(os.path.join(OUT,"mask.json"),"rb").read(3)==b"\xef\xbb\xbf")
print("BOM metrics:", open(os.path.join(OUT,"metrics.json"),"rb").read(3)==b"\xef\xbb\xbf")
print("BOM per_clip:", open(os.path.join(OUT,"per_clip.json"),"rb").read(3)==b"\xef\xbb\xbf")
print("BOM dupes:", open(os.path.join(OUT,"dupes.json"),"rb").read(3)==b"\xef\xbb\xbf")
fj=sum(1 for d,_,fs in os.walk(os.path.join(OUT,"frames")) for f in fs if f.endswith(".jpg"))
print("frames jpg on disk:", fj, " dirs:", len([d for d in os.listdir(os.path.join(OUT,"frames"))]))
kt=sum(r["keep_secs"] for r in pc.values())
print("keep total: %.2f  (>=180 ? %s)" % (kt, kt>=180))
# duration coverage
tot=sum(meta[fn]["n_frames"]*0.5 for fn in meta)
print("total duration %.2f" % tot)
bad=[]
for fn in M:
    if abs(len(M[fn]) - meta[fn]["n_frames"])>0: bad.append(fn)
print("metric/frame count mismatch:", bad or "none")
# check keep windows valid
problems=[]
for fn,r in pc.items():
    for a,b in r["keep"]:
        if b-a < 1.99 or b > r["dur"]+0.01 or a<0: problems.append((fn,a,b,r["dur"]))
print("bad keep windows:", problems[:5] or "none")
print("keys sample per_clip:", list(pc["C1825S03.mp4"].keys()))
print("mask sample:", {k:mask[k] for k in list(mask)[:2]})
print("dupes sample len:", [len(x) for x in dp])
