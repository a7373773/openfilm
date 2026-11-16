# -*- coding: utf-8 -*-
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs"); FR = os.path.join(WORK, "frames")
SH = os.path.join(WORK, "sheets"); os.makedirs(SH, exist_ok=True)
meta = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
FONT = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 18)
FONT2 = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)

groups = [
 ("review_A", ["C1763.MP4","C1768.MP4","C1773.MP4","C1780.MP4","C1783.MP4"]),
 ("review_B", ["C1821.MP4","C1836.MP4","C1848.MP4","C1854.MP4","C1858.MP4"]),
]
TW, TH, NC = 300, 169, 6
for name, clips in groups:
    W = NC*TW; H = len(clips)*(TH+26)+40
    sheet = Image.new("RGB", (W, H), (14,14,14)); dr = ImageDraw.Draw(sheet)
    dr.text((8, 8), name + "  " + " | ".join(clips), fill=(255,255,255), font=FONT2)
    for ri, c in enumerate(clips):
        d = os.path.join(FR, os.path.splitext(c)[0])
        files = sorted(os.listdir(d))
        idxs = [int(round(i*(len(files)-1)/(NC-1))) for i in range(NC)]
        for ci, ix in enumerate(idxs):
            p = os.path.join(d, files[ix])
            im = Image.open(p).convert("RGB").resize((TW, TH))
            sheet.paste(im, (ci*TW, 40+ri*(TH+26)))
            t = "%s @%.1fs" % (c.replace(".MP4","") if ci==0 else "", ix*0.5)
            dr.text((ci*TW+4, 40+ri*(TH+26)+TH+2), t, fill=(230,230,230), font=FONT)
    out = os.path.join(SH, name+".jpg"); sheet.save(out, quality=90)
    print(out)
