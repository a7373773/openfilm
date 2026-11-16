
import json, os, math
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
aux = json.load(open(os.path.join(V,"aux.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
cands = json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8"))
def aget(f,t): return aux.get(f,{}).get(str(t))
def pget(f,t): return pix.get(f.replace(".mp4",""),{}).get(str(t))

print("=== aux signals on suspicious vs good candidates ===")
print("file            seg        L    | p_clear p_blank | sky  botLap lapvar")
for c in cands[:14] + cands[-4:]:
    fr = [aget(c["file"], t) for t in range(c["start_t"], c["end_t"]+1)]
    pf = [pget(c["file"], t) for t in range(c["start_t"], c["end_t"]+1)]
    fr = [x for x in fr if x]; pf = [x for x in pf if x]
    if not fr or not pf: continue
    ac = sum(x["p_clear_scenery"] for x in fr)/len(fr); ab = sum(x["p_blank"] for x in fr)/len(fr)
    print("%-13s %4d-%-4d %.3f | %5.2f   %5.2f  | %.2f %.4f %.4f" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["mean_p_landscape"], ac, ab,
        sum(x["skyfrac"] for x in pf)/len(pf), sum(x["botLap"] for x in pf)/len(pf), sum(x["lapvar"] for x in pf)/len(pf)))

# global correlation p_blank vs objective
def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a)); sb=math.sqrt(sum((x-mb)**2 for x in b))
    return 0 if sa==0 or sb==0 else sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)
rows=[]
for f, rr in aux.items():
    for t, r in rr.items():
        p = pix.get(f.replace(".mp4",""),{}).get(t)
        if p: rows.append((r,p))
print("\np_blank correlations (n=%d):" % len(rows))
for k in ["skyfrac","flatfrac","botLap","lapvar","colorful","mean","edge"]:
    print("   vs %-9s %+.3f" % (k, corr([r["p_blank"] for r,_ in rows],[p[k] for _,p in rows])))
print("p_clear correlations:")
for k in ["skyfrac","flatfrac","botLap","lapvar","colorful","edge"]:
    print("   vs %-9s %+.3f" % (k, corr([r["p_clear_scenery"] for r,_ in rows],[p[k] for _,p in rows])))
# among p_landscape>=0.5, how many blank per aux
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
hi = [(f,t) for f, rr in tags.items() for r in rr if r["p_landscape"]>=0.5 for t in [r["t"]]]
hi_a = [(f,t) for f,t in hi if aget(f,t) and aget(f,t)["p_blank"]>=0.5]
print("\nframes p_landscape>=0.5: %d, of which aux p_blank>=0.5: %d (%.0f%%)" % (len(hi), len(hi_a), 100*len(hi_a)/max(1,len(hi))))
