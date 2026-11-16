
import os, json, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
out=[]
for f in sorted(os.listdir(SRC)):
    if not f.upper().endswith(".MP4"): continue
    p=os.path.join(SRC,f)
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True)
    txt=r.stderr.decode("utf-8","replace")
    dur=None; fps=None; wh=None
    for line in txt.splitlines():
        if "Duration:" in line:
            dur=line.split("Duration:")[1].split(",")[0].strip()
        if "Video:" in line and "h264" in line:
            import re
            m=re.search(r"(\d{3,5})x(\d{3,5})",line); wh=m.group(0) if m else None
            m2=re.search(r"([\d.]+) fps",line); fps=m2.group(1) if m2 else None
    out.append(dict(f=f,dur=dur,wh=wh,fps=fps,size=os.path.getsize(p)))
print(json.dumps(out,ensure_ascii=False,indent=1))
