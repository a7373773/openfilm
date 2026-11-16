
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
def test(name, f, st, extra):
    vf = "trim=start=0:duration=2.0,setpts=PTS-STARTPTS,fps=30,scale=1920:1080:flags=lanczos,setsar=1"
    if extra: vf += ","+extra
    out = os.path.join(WK,"render","dbg3_%s.mp4"%name)
    r = subprocess.run([FF,"-hide_banner","-loglevel","error","-y","-ss","%.3f"%st,"-i",os.path.join(SRC,f),
        "-filter_complex","[0:v]"+vf+"[v]","-map","[v]","-an","-r","30","-frames:v","60",
        "-c:v","libx264","-preset","veryfast","-crf","15","-pix_fmt","yuv420p",out],capture_output=True)
    if r.returncode!=0:
        print("%-28s FAIL %s"%(name, r.stderr.decode("utf-8","replace")[-180:])); return
    p = os.path.join(WK,"render","dbg3_%s.png"%name)
    subprocess.run([FF,"-v","error","-y","-ss","0.5","-i",out,"-frames:v","1",p],check=True)
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    print("%-28s luma=%6.1f std=%5.1f"%(name,Y.mean(),Y.std()))
# dark clip: C1848 (luma 25), bright clip C1873 (luma 223), mid C1828 (136)
test("dark_plain",  "C1848S03.mp4", 8.5, None)
test("dark_curves", "C1848S03.mp4", 8.5, "curves=all='0.10/0 0.62/1 1/1'")
test("dark_eq_g15", "C1848S03.mp4", 8.5, "eq=gamma=1.5:brightness=0.02")
test("bright_plain","C1873S03.mp4", 1.0, None)
test("bright_curves","C1873S03.mp4",1.0, "curves=all='0.12/0 0.92/1 1/1'")
test("mid_curves",  "C1828S03.mp4", 0.5, "curves=all='0.07/0 0.96/1 1/1'")
