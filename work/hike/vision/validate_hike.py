
# -*- coding: utf-8 -*-
import json, os, math, statistics as st, collections
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
aux  = json.load(open(os.path.join(V,"aux.json"), encoding="utf-8"))
pix  = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))

def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a)); sb=math.sqrt(sum((y-mb)**2 for y in b))
    return 0.0 if sa==0 or sb==0 else sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)

rows=[]
for clip, rr in tags.items():
    c = clip.replace(".mp4","")
    ax = {r["seq"]: r for r in aux.get(c, [])}
    for r in rr:
        seq = int(round(r["t"]/0.5))+1
        p = pix.get(c,{}).get(str(seq))
        a = ax.get(seq)
        if p and a: rows.append((clip, seq, r, a, p))
print("joined frames:", len(rows), "clips:", len(tags))

def col(name): return [x[2][name] for x in rows]
def pixcol(k): return [x[4][k] for x in rows]
def auxcol(k): return [x[3][k] for x in rows]

print("\n== overall distribution ==")
for k in ["p_person","p_people","p_back","p_landscape","p_clear","p_blocked","p_closeup","p_blurry"]:
    v = col(k)
    print("  %-11s mean %.3f  median %.3f  >=0.5: %4d (%.1f%%)" % (k, sum(v)/len(v), st.median(v), sum(1 for x in v if x>=0.5), 100*sum(1 for x in v if x>=0.5)/len(v)))
sc = collections.Counter(x[2]["scene"] for x in rows)
print("  scenes:", dict(sc.most_common()))

print("\n== internal consistency: presence vs backview group ==")
print("  corr(p_person, p_back+p_front) = %.3f" % corr(col("p_person"), [a+b for a,b in zip(col("p_back"), col("p_front"))]))
print("  corr(p_person, p_nobody)       = %.3f" % corr(col("p_person"), col("p_nobody")))
print("\n== second-opinion aux agreement ==")
print("  corr(p_person,   p_human)  = %.3f" % corr(col("p_person"), auxcol("p_human")))
print("  corr(p_closeup,  p_ground2)= %.3f" % corr(col("p_closeup"), auxcol("p_ground2")))
print("  corr(p_landscape,p_wide2)  = %.3f" % corr(col("p_landscape"), auxcol("p_wide2")))
print("  corr(p_closeup,  p_bag2)   = %.3f" % corr(col("p_closeup"), auxcol("p_bag2")))
print("\n== vs objective pixel stats ==")
for k in ["p_person","p_landscape","p_closeup","p_blocked","p_blurry"]:
    print("  %-11s" % k, " ".join("%s %+.2f" % (kk, corr(col(k), pixcol(kk))) for kk in ["skin","edge","lapvar","skyfrac","greenfrac","botLap","topLap","colorful","mean"]))

print("\n== per-clip quick view (sorted by mean p_person desc, 15) ==")
perclip = {}
for clip, rr in tags.items():
    perclip[clip] = {
        "n": len(rr),
        "person": sum(r["p_person"] for r in rr)/len(rr),
        "back": sum(r["p_back"] for r in rr)/len(rr),
        "land": sum(r["p_landscape"] for r in rr)/len(rr),
        "close": sum(r["p_closeup"] for r in rr)/len(rr),
        "block": sum(r["p_blocked"] for r in rr)/len(rr),
        "blur": sum(r["p_blurry"] for r in rr)/len(rr),
        "person_r": sum(1 for r in rr if r["p_person"]>=0.5)/len(rr),
        "back_r": sum(1 for r in rr if r["p_back"]>=0.5)/len(rr),
        "ground_r": sum(1 for r in rr if r["p_closeup"]>=0.5)/len(rr),
        "scene": collections.Counter(r["scene"] for r in rr).most_common(1)[0][0],
    }
for clip,v in sorted(perclip.items(), key=lambda kv: -kv[1]["person"])[:15]:
    print("  %-12s n=%2d person=%.2f(%.0f%%) back=%.2f land=%.2f close=%.2f block=%.2f scene=%s" % (
        clip.replace(".mp4",""), v["n"], v["person"], 100*v["person_r"], v["back"], v["land"], v["close"], v["block"], v["scene"]))
print("  ... lowest 8 by person:")
for clip,v in sorted(perclip.items(), key=lambda kv: kv[1]["person"])[:8]:
    print("  %-12s n=%2d person=%.2f land=%.2f close=%.2f scene=%s" % (clip.replace(".mp4",""), v["n"], v["person"], v["land"], v["close"], v["scene"]))
