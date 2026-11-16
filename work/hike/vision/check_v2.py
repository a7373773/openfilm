
# -*- coding: utf-8 -*-
import json, os, math, statistics as st, collections
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
aux  = json.load(open(os.path.join(V,"aux.json"), encoding="utf-8"))
pix  = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
rows=[]
for clip, rr in tags.items():
    c = clip.replace(".mp4","")
    ax = {r["seq"]: r for r in aux.get(c, [])}
    for r in rr:
        seq = int(round(r["t"]/0.5))+1
        p = pix.get(c,{}).get(str(seq)); a = ax.get(seq)
        if p and a: rows.append((c, seq, r, a, p))
def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a)); sb=math.sqrt(sum((y-mb)**2 for y in b))
    return 0.0 if sa==0 or sb==0 else sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)
def col(k): return [x[2][k] for x in rows]
def pixc(k): return [x[4][k] for x in rows]
def auxc(k): return [x[3][k] for x in rows]

print("== v2 distribution (n=%d) ==" % len(rows))
for k in ["p_person","p_people","p_back","p_facing","p_trail_ahead","p_wide_vista","p_landscape","p_clear","p_blocked","p_closeup","p_blurry"]:
    v=col(k); print("  %-14s mean %.3f med %.3f  >=0.5 %4d (%.1f%%)" % (k, sum(v)/len(v), st.median(v), sum(1 for x in v if x>=0.5), 100*sum(1 for x in v if x>=0.5)/len(v)))

print("\n== ground class validation vs geometry rule ==")
strict = [x for x in rows if x[4]["skyfrac"]<0.05 and x[4]["topLap"]>0.015 and abs(x[4]["vertGrad"])<0.08]
strict_set = set((x[0], x[1]) for x in strict)
rest = [x for x in rows if (x[0],x[1]) not in strict_set]
print("  geometry-ground frames n=%d: mean p_closeup %.2f, mean p_person %.2f, mean p_landscape %.2f" % (
    len(strict), sum(x[2]["p_closeup"] for x in strict)/len(strict), sum(x[2]["p_person"] for x in strict)/len(strict), sum(x[2]["p_landscape"] for x in strict)/len(strict)))
print("  other frames      n=%d: mean p_closeup %.2f, mean p_person %.2f, mean p_landscape %.2f" % (
    len(rest), sum(x[2]["p_closeup"] for x in rest)/len(rest), sum(x[2]["p_person"] for x in rest)/len(rest), sum(x[2]["p_landscape"] for x in rest)/len(rest)))
print("  corr(p_closeup, skyfrac) = %+.3f   corr(p_closeup, vertGrad) = %+.3f" % (corr(col("p_closeup"), pixc("skyfrac")), corr(col("p_closeup"), pixc("vertGrad"))))
print("  corr(p_wide_vista, skyfrac) = %+.3f  corr(p_landscape, skyfrac) = %+.3f" % (corr(col("p_wide_vista"), pixc("skyfrac")), corr(col("p_landscape"), pixc("skyfrac"))))

print("\n== second-opinion aux agreement ==")
for a,b in [("p_person","p_human"),("p_closeup","p_ground2"),("p_landscape","p_wide2"),("p_wide_vista","p_wide2")]:
    print("  corr(%-13s, %-8s) = %+.3f" % (a, b, corr(col(a), auxc(b))))

print("\n== vs objective ==")
for k in ["p_person","p_back","p_closeup","p_wide_vista","p_landscape","p_blurry","p_blocked"]:
    print("  %-13s" % k, " ".join("%s %+.2f" % (kk, corr(col(k), pixc(kk))) for kk in ["skin","edge","lapvar","skyfrac","greenfrac","botLap","topLap","colorful","vertGrad"]))

print("\n== per-clip means (top/bottom by person, ground, vista) ==")
pc={}
for clip, rr in tags.items():
    d = lambda k: sum(r[k] for r in rr)/len(rr)
    pc[clip] = dict(n=len(rr), person=d("p_person"), people=d("p_people"), back=d("p_back"), trail=d("p_trail_ahead"),
                    ground=d("p_closeup"), vista=d("p_wide_vista"), land=d("p_landscape"), block=d("p_blocked"), blur=d("p_blurry"),
                    scene=collections.Counter(r["scene"] for r in rr).most_common(1)[0][0],
                    back_r=sum(1 for r in rr if r["p_back"]>=0.5)/len(rr),
                    ground_r=sum(1 for r in rr if r["p_closeup"]>=0.5)/len(rr),
                    vista_r=sum(1 for r in rr if r["p_wide_vista"]>=0.5)/len(rr))
print("  --- highest ground (likely waste) ---")
for c,v in sorted(pc.items(), key=lambda kv: -kv[1]["ground"])[:10]:
    print("  %-11s n=%2d ground=%.2f(%.0f%%) person=%.2f land=%.2f block=%.2f scene=%s" % (c.replace(".mp4",""), v["n"], v["ground"], 100*v["ground_r"], v["person"], v["land"], v["block"], v["scene"]))
print("  --- highest back-view ---")
for c,v in sorted(pc.items(), key=lambda kv: -kv[1]["back"])[:10]:
    print("  %-11s n=%2d back=%.2f(%.0f%%) person=%.2f land=%.2f scene=%s" % (c.replace(".mp4",""), v["n"], v["back"], 100*v["back_r"], v["person"], v["land"], v["scene"]))
print("  --- highest vista ---")
for c,v in sorted(pc.items(), key=lambda kv: -kv[1]["vista"])[:10]:
    print("  %-11s n=%2d vista=%.2f(%.0f%%) land=%.2f person=%.2f scene=%s" % (c.replace(".mp4",""), v["n"], v["vista"], 100*v["vista_r"], v["land"], v["person"], v["scene"]))
json.dump({k: v for k, v in pc.items()}, open(os.path.join(V,"_tmp_pc.json"),"w"), ensure_ascii=False)
