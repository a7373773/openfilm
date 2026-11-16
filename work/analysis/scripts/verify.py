import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(OUT,"meta.json"), encoding="utf-8"))
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
from PIL import Image
req = {"t","luma","lumastd","sharp","grad","sat","colorful","darkfrac","brightfrac","entropy","uniform","flatfrac","diff","edgefrac","warmfrac","fineratio"}
bad = []
print("%-16s %6s %5s %5s %6s %7s %7s" % ("file","dur","part","jpg","sheet","rows","ok"))
for fn in sorted(M):
    stem = os.path.splitext(fn)[0]
    n = len(M[fn]); part = meta[fn]["n_frames"]
    jpg = len([f for f in os.listdir(os.path.join(OUT,"frames",stem)) if f.endswith(".jpg")])
    dur = meta[fn]["duration"]
    sp = os.path.join(OUT,"sheets",stem+".jpg")
    ok = True
    if not os.path.exists(sp): ok=False
    else:
        im = Image.open(sp); w,h = im.size
        if w != 1920 or h != meta[fn]["rows"]*108: ok=False
    if not os.path.exists(os.path.join(OUT,"sheets",stem+".txt")): ok=False
    miss = req - set(M[fn][0].keys())
    if miss: ok=False; bad.append((fn, "missing keys "+str(miss)))
    if n != part or jpg != part: ok=False; bad.append((fn,"count mismatch %d/%d/%d"%(n,part,jpg)))
    if abs(n - dur) > 2: ok=False; bad.append((fn,"dur mismatch n=%d dur=%.2f"%(n,dur)))
    if not ok: print("BAD", fn)
print("files:", len(M), " total frames:", sum(len(M[f]) for f in M))
print("problems:", bad if bad else "none")
print("summary exists:", os.path.exists(os.path.join(OUT,"SUMMARY.md")), os.path.getsize(os.path.join(OUT,"SUMMARY.md")))
tot=0
for d,_,fs in os.walk(os.path.join(OUT,"frames")):
    for f in fs: tot += os.path.getsize(os.path.join(d,f))
print("frames total MB: %.1f" % (tot/1048576))
print("sheets MB: %.1f" % (sum(os.path.getsize(os.path.join(OUT,"sheets",f)) for f in os.listdir(os.path.join(OUT,"sheets")))/1048576))
