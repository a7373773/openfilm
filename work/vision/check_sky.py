
import json, os, statistics as st
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
cands = json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8"))

def pget(f,t):
    return pix.get(f.replace(".mp4",""),{}).get(str(t))

def agg(frames):
    keys = ["skyfrac","flatfrac","botLap","topLap","colorful","mean","edge","greenfrac","lapvar","std"]
    out = {}
    for k in keys:
        vals = [p[k] for p in frames if p]
        out[k] = round(sum(vals)/len(vals), 4) if vals else -1
    return out

# top candidates pixel profile
print("=== top 10 candidates: pixel profile ===")
print("file            seg        L    | sky  flat botLap colorful mean edge green lapvar")
for c in cands[:10]:
    fr = [pget(c["file"], t) for t in range(c["start_t"], c["end_t"]+1)]
    a = agg(fr)
    print("%-13s %4d-%-4d %.3f | %.2f %.2f %.4f  %.3f  %.2f %.3f %.2f %.4f" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["mean_p_landscape"],
        a["skyfrac"], a["flatfrac"], a["botLap"], a["colorful"], a["mean"], a["edge"], a["greenfrac"], a["lapvar"]))

# all frames profile by p_landscape decile
rows = []
for f, rr in tags.items():
    for r in rr:
        p = pget(f, r["t"])
        if p: rows.append((r["p_landscape"], r["p_blocked"], p))
rows.sort()
n = len(rows)
print("\n=== pixel profile by p_landscape decile (n=%d) ===" % n)
print("decile   mean   | sky  flat botLap colorful mean edge green lapvar pBlk")
for i in range(10):
    part = rows[int(i*n/10):int((i+1)*n/10)]
    a = agg([p for _,_,p in part])
    print("d%d %5.2f | %.2f %.2f %.4f  %.3f  %.2f %.3f %.2f %.4f %.2f" % (
        i+1, sum(x[0] for x in part)/len(part), a["skyfrac"], a["flatfrac"], a["botLap"], a["colorful"],
        a["mean"], a["edge"], a["greenfrac"], a["lapvar"], sum(x[1] for x in part)/len(part)))

# blank-sky suspicion: frames with skyfrac>0.9 and botLap<0.01 (nothing but sky/no detail)
blank = [r for _,_,r in rows if r["skyfrac"]>0.9 and r["botLap"]<0.005]
print("\nframes ~pure sky/no detail (skyfrac>0.9, botLap<0.005):", len(blank))
# how many high-p_landscape frames are in that bucket
hi = [r for r,a,b in rows if a>=0.5]
hib = [r for r in hi if r["skyfrac"]>0.9 and r["botLap"]<0.005]
print("  of %d frames with p_landscape>=0.5, %d (%.0f%%) are near-featureless sky" % (len(hi), len(hib), 100*len(hib)/max(1,len(hi))))
# detailed frames (botLap high) with high p_landscape
hd = [r for r in hi if r["botLap"]>0.02]
print("  of those, %d have real bottom-half detail (botLap>0.02)" % len(hd))
