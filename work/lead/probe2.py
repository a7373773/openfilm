
import subprocess, os, re, json
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
rows=[]
tot=0
for f in files:
    p=os.path.join(SRC,f)
    out=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    m=re.search(r"Duration: (\d+):(\d+):([\d.]+)",out)
    d=int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3)) if m else 0
    v=re.search(r"Video: (\S+)[^\n]*?(\d{3,4})x(\d{3,4})[^\n]*?([\d.]+) fps",out)
    a="Audio:" in out
    rows.append(dict(f=f,dur=round(d,2),w=int(v.group(2)) if v else 0,h=int(v.group(3)) if v else 0,
                     fps=float(v.group(4)) if v else 0,audio=a,size=os.path.getsize(p)))
    tot+=d
json.dump(rows,open(r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work2_probe.json","w"),ensure_ascii=False,indent=1)
print("files",len(rows),"total dur %.1f s (%.2f min)"%(tot,tot/60))
print("res/fps set:", set((r["w"],r["h"]) for r in rows), set(r["fps"] for r in rows))
print("with audio:", sum(1 for r in rows if r["audio"]))
ds=[r["dur"] for r in rows]
print("dur min/med/max: %.2f / %.2f / %.2f"%(min(ds),sorted(ds)[len(ds)//2],max(ds)))
print("dur hist:", {k:sum(1 for d in ds if k<=d<k+2) for k in range(0,22,2)})
print()
for r in rows: print("%-14s %6.2fs %dx%d %.0ffps a=%s"%(r["f"],r["dur"],r["w"],r["h"],r["fps"],r["audio"]))
