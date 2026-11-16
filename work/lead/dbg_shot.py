
import json, subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
edl = json.load(open(os.path.join(WK,"edl.json"),encoding="utf-8-sig"))
s = edl["shots"][1]
print("shot1:", s["file"], s["start"], s["dur"], "levels:", s["levels"])
LOOK = ("curves=all='0/0.008 0.25/0.252 0.5/0.520 0.80/0.812 1/0.930',"
        "eq=saturation=1.04:contrast=1.04:gamma=1.01,"
        "vibrance=0.10,"
        "colorbalance=rs=-0.008:gs=0.004:bs=0.020:rh=0.016:gh=0.004:bh=-0.010")
def test(name, extra):
    vf = "trim=start=0:duration=3.0,setpts=PTS-STARTPTS,fps=30,scale=1920:1080:flags=lanczos,setsar=1"
    if extra: vf += ","+extra
    out = os.path.join(WK,"render","dbg_%s.mp4"%name)
    r = subprocess.run([FF,"-hide_banner","-loglevel","error","-y","-ss","%.3f"%s["start"],"-i",os.path.join(SRC,s["file"]),
        "-filter_complex","[0:v]"+vf+"[v]","-map","[v]","-an","-r","30","-frames:v","90",
        "-c:v","libx264","-preset","veryfast","-crf","15","-pix_fmt","yuv420p",out],capture_output=True)
    if r.returncode!=0:
        print(name,"FAIL",r.stderr.decode("utf-8","replace")[-300:]); return
    p = os.path.join(WK,"render","dbg_%s.png"%name)
    subprocess.run([FF,"-v","error","-y","-ss","0.5","-i",out,"-frames:v","1",p],check=True)
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    print("%-22s luma=%6.1f std=%5.1f"%(name,Y.mean(),Y.std()))
test("plain", None)
test("look_only", LOOK)
lv = s["levels"]
cl = "colorlevels=rimin=%.4f:rimax=%.4f:gimin=%.4f:gimax=%.4f:bimin=%.4f:bimax=%.4f"%tuple(lv)
test("levels_only", cl)
test("levels_look", cl+","+LOOK)
