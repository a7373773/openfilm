# -*- coding: utf-8 -*-
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WORK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\zs"
M = os.path.join(WORK, "zhongshan_master.mp4")
EDL = json.load(open(os.path.join(WORK,"edl.json"),encoding="utf-8")); T = EDL["total"]
info = subprocess.run([FF,"-hide_banner","-i",M],stdout=subprocess.PIPE,stderr=subprocess.PIPE).stderr.decode("utf-8","replace")
for line in info.splitlines():
    if "Duration" in line or "Stream" in line: print(line.strip()[:150])
F = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 15)
TW,TH,COLS = 400,225,5
times = [round(i*T/39,2) for i in range(40)]
rows = (len(times)+COLS-1)//COLS
sheet = Image.new("RGB",(TW*COLS,(TH+20)*rows),(10,10,10)); dr = ImageDraw.Draw(sheet)
for k,tt in enumerate(times):
    j = os.path.join(WORK,"rv_%03d.jpg"%k)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%tt,"-i",M,"-frames:v","1","-q:v","4",j])
    if os.path.exists(j):
        sheet.paste(Image.open(j).convert("RGB").resize((TW,TH)),((k%COLS)*TW,(k//COLS)*(TH+20)))
    dr.text(((k%COLS)*TW+4,(k//COLS)*(TH+20)+TH+2),"%d:%05.1f"%((int(tt//60)),tt%60),fill=(240,240,240),font=F)
out = os.path.join(WORK,"sheets","timeline_review.jpg"); sheet.save(out,quality=86)
print(out, sheet.size)
