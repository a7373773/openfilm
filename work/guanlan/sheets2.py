
import os, subprocess, json
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
TMP = r"C:\Users\30308\AppData\Local\Temp\glwork"
os.makedirs(TMP, exist_ok=True)
FILES = sorted(f for f in os.listdir(SRC) if f.upper().endswith(".MP4"))
info={}
for f in FILES:
    p=os.path.join(SRC,f)
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True)
    t=r.stderr.decode("utf-8","replace")
    import re
    dur=re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",t)
    d=int(dur.group(1))*3600+int(dur.group(2))*60+float(dur.group(3))
    m=re.search(r"Video: .*?(\d{3,5})x(\d{3,5})",t)
    fps=re.search(r"([\d.]+) fps",t).group(1)
    n=12
    step=max(1,d/n)
    outp=os.path.join(TMP,f.replace(".MP4","")+ ".jpg")
    vf="fps=%.4f,scale=380:-2,tile=4x3"%(1.0/step)
    subprocess.run([FF,"-hide_banner","-loglevel","error","-y","-i",p,"-vf",vf,"-frames:v","1",outp],capture_output=True)
    info[f]=dict(dur=round(d,2),wh=m.group(0) if m else None,fps=fps,sheet=outp,ok=os.path.exists(outp))
print(json.dumps(info,indent=1))
