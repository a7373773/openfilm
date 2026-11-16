import os, sys, json
sys.path.insert(0, "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/scripts")
import numpy as np
from PIL import Image
FR = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/frames"
PT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/parts"
def lapvar(g):
    p = np.pad(g,1,mode="edge")
    lap = p[:-2,1:-1]+p[2:,1:-1]+p[1:-1,:-2]+p[1:-1,2:]-4.0*g
    return float(lap.var())
out = []
for fn in ("REC-0007-A","REC-0001-A","REC-0005-A","REC-0013-A","REC-0017-A","REC-0006-A"):
    D = json.load(open(os.path.join(PT, fn + ".json"), encoding="utf-8"))
    fr = D["frames"]
    out.append("=== %s ===" % fn)
    for t in range(0, len(fr), 6):
        im = Image.open(os.path.join(FR, fn, "sec_%04d.jpg" % (t+1))).convert("L")
        g = np.asarray(im, dtype=np.float32)
        g2 = np.asarray(im.resize((240,135), Image.LANCZOS), dtype=np.float32)
        L1 = lapvar(g); L2 = lapvar(g2)
        out.append("  t=%3d sharp480=%7.0f L480=%8.0f L240=%8.0f ratio=%5.2f" % (t, fr[t]["sharp"], L1, L2, L1/max(4.0*L2,1e-6)))
open("D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/logs/octave.txt","w",encoding="utf-8").write("\n".join(out))
print("done", len(out))
