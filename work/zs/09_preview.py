# -*- coding: utf-8 -*-
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WORK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\zs"
EDL = json.load(open(os.path.join(WORK,"edl.json"),encoding="utf-8"))
shots = {s["i"]: s for s in EDL["shots"]}
ids = [int(x) for x in sys.argv[1].split(",")]
out = os.path.join(WORK,"sheets","graded_test.jpg")
F = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 18)
TW,TH = 600,338
sheet = Image.new("RGB",(TW*2, TH*((len(ids)+1)//2)+26*((len(ids)+1)//2)+30),(12,12,12))
dr = ImageDraw.Draw(sheet)
for k,i in enumerate(ids):
    s = shots[i]; p = os.path.join(WORK,"clips","shot_%02d.mp4"%i)
    t = os.path.join(WORK,"t_%02d.jpg"%i)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%(s["dur"]*0.5),"-i",p,"-frames:v","1","-q:v","2",t])
    if os.path.exists(t):
        im = Image.open(t).convert("RGB").resize((TW,TH))
        cx,cy = (k%2)*TW, (k//2)*(TH+26)+26
        sheet.paste(im,(cx,cy))
        dr.text((cx+6,cy-22), "#%02d %s  sh=%.0f p50=%.0f" % (i, s["file"], s["sharp"], s["p50"]), fill=(240,240,240), font=F)
sheet.save(out, quality=90); print(out)
