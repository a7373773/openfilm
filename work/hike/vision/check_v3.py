
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

print("== view group distribution (frames) ==")
vc = collections.Counter(x[2]["view"] for x in rows)
for k,v in vc.most_common(): print("   %-11s %4d (%.1f%%)" % (k, v, 100*v/len(rows)))
print("\n== scene distribution ==")
sc = collections.Counter(x[2]["scene"] for x in rows)
for k,v in sc.most_common(): print("   %-9s %4d (%.1f%%)" % (k, v, 100*v/len(rows)))

print("\n== key means ==")
for k in ["p_person","p_people","p_back","p_back_far","p_back_close","p_facing","p_trail_ahead","p_ground","p_wide_vista","p_landscape","p_clear","p_blocked","p_blurry"]:
    v=col(k); print("  %-14s mean %.3f med %.3f >=0.5 %4d (%.1f%%)" % (k, sum(v)/len(v), st.median(v), sum(1 for x in v if x>=0.5), 100*sum(1 for x in v if x>=0.5)/len(v)))

# physical "pointing at dirt ground" rule: no sky, little green, top darker than bottom
phys = [x for x in rows if x[4]["skyfrac"]<0.03 and x[4]["greenfrac"]<0.20 and x[4]["vertGrad"]<0.02]
phys_ids = set((x[0],x[1]) for x in phys)
print("\n== physical ground rule (no sky + little green + flat/dark top): %d frames (%.1f%%) ==" % (len(phys), 100*len(phys)/len(rows)))
print("   those frames: mean p_ground %.2f  mean p_back_close %.2f  mean p_landscape %.2f  mean cobble?" % (
    sum(x[2]["p_ground"] for x in phys)/max(1,len(phys)), sum(x[2]["p_back_close"] for x in phys)/max(1,len(phys)), sum(x[2]["p_landscape"] for x in phys)/max(1,len(phys))))
print("   corr(p_ground, phys-rule indicator) = %+.3f" % corr(col("p_ground"), [1.0 if (c,s) in phys_ids else 0.0 for c,s,_,_,_ in rows]))
print("   corr(p_ground, skyfrac) %+.3f | greenfrac %+.3f | vertGrad %+.3f" % (corr(col("p_ground"), pixc("skyfrac")), corr(col("p_ground"), pixc("greenfrac")), corr(col("p_ground"), pixc("vertGrad"))))
print("\n== wide vista validation ==")
print("   corr(p_wide_vista, skyfrac) %+.3f | aux p_wide2 %+.3f | p_blocked %+.3f" % (corr(col("p_wide_vista"), pixc("skyfrac")), corr(col("p_wide_vista"), auxc("p_wide2")), corr(col("p_wide_vista"), col("p_blocked"))))
print("   corr(p_back_close, greenfrac) %+.3f | p_ground %+.3f" % (corr(col("p_back_close"), pixc("greenfrac")), corr(col("p_back_close"), col("p_ground"))))
print("\n== aux agreement ==")
print("   corr(p_person, p_human) %+.3f | corr(p_ground, p_ground2) %+.3f | corr(p_landscape, p_wide2) %+.3f" % (
    corr(col("p_person"), auxc("p_human")), corr(col("p_ground"), auxc("p_ground2")), corr(col("p_landscape"), auxc("p_wide2"))))

print("\n== blur sanity ==")
for lo,hi,name in [(0.7,1.1,"p_blurry>=0.7"),(0.4,0.7,"0.4-0.7"),(0,0.4,"<0.4")]:
    v=[x for x in rows if lo<=x[2]["p_blurry"]<hi]
    if v: print("   %-14s n=%3d lapvar %.4f edge %.3f p_clear %.2f" % (name, len(v), sum(x[4]["lapvar"] for x in v)/len(v), sum(x[4]["edge"] for x in v)/len(v), sum(x[2]["p_clear"] for x in v)/len(v)))

print("\n== per-clip (sorted by mean p_ground desc) ==")
pc={}
for clip, rr in tags.items():
    d = lambda k: sum(r[k] for r in rr)/len(rr)
    pc[clip]=dict(n=len(rr), person=d("p_person"), people=d("p_people"), back=d("p_back"), back_far=d("p_back_far"), back_close=d("p_back_close"),
        ground=d("p_ground"), vista=d("p_wide_vista"), ahead=d("p_trail_ahead"), land=d("p_landscape"), block=d("p_blocked"), blur=d("p_blurry"),
        view=collections.Counter(r["view"] for r in rr).most_common(1)[0][0], scene=collections.Counter(r["scene"] for r in rr).most_common(1)[0][0],
        back_r=sum(1 for r in rr if r["p_back"]>=0.5)/len(rr), ground_r=sum(1 for r in rr if r["p_ground"]>=0.5)/len(rr),
        vista_r=sum(1 for r in rr if r["p_wide_vista"]>=0.5)/len(rr), block_r=sum(1 for r in rr if r["p_blocked"]>=0.5)/len(rr))
for c,v in sorted(pc.items(), key=lambda kv: -kv[1]["ground"])[:12]:
    print("  %-11s n=%2d ground=%.2f(%.0f%%) backclose=%.2f person=%.2f land=%.2f block=%.2f scene=%-7s view=%s" % (
        c.replace(".mp4",""), v["n"], v["ground"], 100*v["ground_r"], v["back_close"], v["person"], v["land"], v["block"], v["scene"], v["view"]))
print("  --- highest vista ---")
for c,v in sorted(pc.items(), key=lambda kv: -kv[1]["vista"])[:12]:
    print("  %-11s n=%2d vista=%.2f(%.0f%%) land=%.2f person=%.2f scene=%-7s view=%s" % (c.replace(".mp4",""), v["n"], v["vista"], 100*v["vista_r"], v["land"], v["person"], v["scene"], v["view"]))
json.dump(pc, open(os.path.join(V,"_tmp_pc.json"),"w"), ensure_ascii=False)
