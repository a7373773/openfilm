import json,sys,os
P=r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\parts"
for stem in ["REC-0023-A","REC-0004-A"]:
    d=json.load(open(os.path.join(P,stem+".json"),encoding="utf-8"))
    print(d["file"], "dur",d["duration"],"n",d["n_frames"])
    for f in d["frames"]:
        print("  t=%3d luma=%6.1f std=%5.1f sharp=%8.0f grad=%5.1f sat=%.3f colf=%5.1f dark=%.3f ent=%4.2f uni=%.2f flat=%.2f diff=%5.2f" % (
            f["t"],f["luma"],f["lumastd"],f["sharp"],f["grad"],f["sat"],f["colorful"],f["darkfrac"],f["entropy"],f["uniform"],f["flatfrac"],f["diff"]))
