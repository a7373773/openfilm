# -*- coding: utf-8 -*-
import os, json, math
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
M = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
print("%-14s %5s | %6s %6s %6s %6s %6s %6s %6s" % ("file","n","luma","stdsd","sharp","finer","edge","uni","diff"))
rows=[]
for fn in sorted(M):
    fr=M[fn]
    a=lambda k: float(np.mean([f[k] for f in fr]))
    rows.append((fn, len(fr), a("luma"), a("lumastd"), a("sharp"), a("fineratio"), a("edgefrac"), a("uniform"), a("diff")))
for r in rows:
    print("%-14s %5d | %6.0f %6.0f %6.0f %6.3f %6.3f %6.2f %6.1f" % r)
print()
print("=== batch distribution ===")
for k,i in (("luma",2),("sharp",4),("fineratio",5),("edgefrac",6)):
    v=sorted(r[i] for r in rows)
    print("%-10s min=%.3f p05=%.3f p25=%.3f med=%.3f p75=%.3f max=%.3f" % (k, v[0], v[int(.05*len(v))], v[int(.25*len(v))], v[len(v)//2], v[int(.75*len(v))], v[-1]))
print()
dark=[r[0] for r in rows if r[4] < 500 or r[2] < 70]
print("suspect dark/lowdetail clips:", len(dark), dark)
