import json,os
OUT=r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
pc=json.load(open(os.path.join(OUT,"per_clip.json"),encoding="utf-8"))
order=sorted(pc)
c=[f.replace("S03.mp4","") for f in order if pc[f]["grade"]=="C" and pc[f]["keep"]]
a=[f.replace("S03.mp4","") for f in order if pc[f]["grade"]=="A" and pc[f]["keep"]]
b=[f.replace("S03.mp4","") for f in order if pc[f]["grade"]=="B" and pc[f]["keep"]]
print("A(%d): %s" % (len(a), "、".join(a)))
print("B(%d): %s" % (len(b), "、".join(b)))
print("C(%d): %s" % (len(c), "、".join(c)))
dark=[(f.replace("S03.mp4",""), pc[f]["mean_luma"]) for f in order if pc[f]["mean_luma"]<80]
print("luma<80:", dark)
