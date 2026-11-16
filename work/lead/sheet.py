
# -*- coding: utf-8 -*-
"""Contact sheet: one labelled thumbnail per shot, taken from the final render."""
import subprocess, os, json
from PIL import Image, ImageDraw, ImageFont
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片"
os.makedirs(OUT, exist_ok=True)
TMP = os.path.join(W, "lead", "sheet_tiles")
os.makedirs(TMP, exist_ok=True)
edl = json.load(open(os.path.join(W, "lead", "edl.json"), encoding="utf-8-sig"))
shots = edl["shots"]
XSECS = 0.5

# timeline positions
pos = []
t = 0.0
for i, s in enumerate(shots):
    pos.append((i, t, s["file"], s.get("scene")))
    t = t + s["dur"] - s.get("xfade", 0.0)

final = os.path.join(W, "render", "master_v3_crf21.mp4")
tiles = []
for (i, st, f, sc) in pos:
    mid = st + shots[i]["dur"] / 2.0
    out = os.path.join(TMP, "t_%02d.jpg" % i)
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.2f" % mid, "-i", final,
                    "-frames:v", "1", "-q:v", "2", out], check=True)
    tiles.append(out)

TW, TH = 480, 270
COLS = 3
ROWS = (len(tiles) + COLS - 1) // COLS
PAD = 8
LABEL_H = 34
Wt = COLS * TW + (COLS + 1) * PAD
Ht = ROWS * (TH + LABEL_H) + (ROWS + 1) * PAD
sheet = Image.new("RGB", (Wt, Ht), (18, 18, 20))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
for k, p in enumerate(tiles):
    r_, c_ = divmod(k, COLS)
    x = PAD + c_ * (TW + PAD)
    y = PAD + r_ * (TH + LABEL_H + PAD)
    im = Image.open(p).convert("RGB").resize((TW, TH), Image.LANCZOS)
    sheet.paste(im, (x, y))
    i, st = pos[k][0], pos[k][1]
    scene = shots[i].get("scene") or "-"
    lab = "#%02d  %d:%04.1f  %s" % (i + 1, int(st // 60), st - 60 * int(st // 60), scene)
    d.text((x + 6, y + TH + 6), lab, fill=(235, 235, 235), font=font)
sheet.save(os.path.join(OUT, "预览_分镜缩略图.jpg"), quality=88)
print("sheet", sheet.size, os.path.join(OUT, "预览_分镜缩略图.jpg"))
