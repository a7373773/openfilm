# -*- coding: utf-8 -*-
"""Contact sheet + verification for the hike montage."""
import subprocess, os, json, sys
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\爬山"
os.makedirs(OUT, exist_ok=True)
final = os.path.join(WK, "render", "hike_v3.mp4")
edl = json.load(open(os.path.join(WK, "edl.json"), encoding="utf-8-sig"))
shots = edl["shots"]
pos, t = [], 0.0
for i, s in enumerate(shots):
    pos.append((i, t)); t += float(s["dur"]) - float(s.get("trans", 0.0) or 0.0)
TOTAL = t
print("total %.2f  shots %d" % (TOTAL, len(shots)))

TMP = os.path.join(WK, "render", "tiles"); os.makedirs(TMP, exist_ok=True)
tiles = []
for (i, st) in pos:
    mid = st + float(shots[i]["dur"]) / 2.0
    p = os.path.join(TMP, "t_%02d.jpg" % i)
    r = subprocess.run([FF, "-v", "error", "-y", "-ss", "%.2f" % mid, "-i", final, "-frames:v", "1", "-q:v", "2", p],
                       capture_output=True)
    if r.returncode == 0 and os.path.exists(p): tiles.append((i, st, p))

TW, TH, COLS, PAD, LH = 400, 225, 5, 8, 30
ROWS = (len(tiles) + COLS - 1) // COLS
W = COLS * TW + (COLS + 1) * PAD; H = ROWS * (TH + LH) + (ROWS + 1) * PAD
sheet = Image.new("RGB", (W, H), (16, 16, 18)); d = ImageDraw = None
from PIL import ImageDraw, ImageFont
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
for k, (i, st, p) in enumerate(tiles):
    r_, c_ = divmod(k, COLS)
    x = PAD + c_ * (TW + PAD); y = PAD + r_ * (TH + LH + PAD)
    sheet.paste(Image.open(p).convert("RGB").resize((TW, TH), Image.LANCZOS), (x, y))
    d.text((x + 5, y + TH + 5), "#%02d  %d:%04.1f" % (i + 1, int(st // 60), st - 60 * int(st // 60)),
           fill=(235, 235, 235), font=font)
sheet.save(os.path.join(OUT, "预览_分镜缩略图.jpg"), quality=86)
print("sheet", sheet.size)
