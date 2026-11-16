
# -*- coding: utf-8 -*-
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\观澜版画村"
V = os.path.join(OUT, "一版秋花_画质版_1080p.mp4")
SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
F = lambda s: ImageFont.truetype(SERIF, s)

def grab(t, name, w=1920):
    p = os.path.join(T, name)
    subprocess.run([FF,"-v","error","-y","-ss","%.3f"%t,"-i",V,"-frames:v","1","-vf","scale=%d:-2"%w,p],check=True)
    return p

# ---------- 分镜缩略图 ----------
times = [1.2,3.5,5.9,8.3,10.7,13.1,15.5,17.9,20.2,22.6,25.0,27.3]
shot_of = [1,2,3,4,5,6,7,8,9,9,9,10]
TW, cols, rows = 480, 4, 3
tiles=[]
for i,(t,sn) in enumerate(zip(times, shot_of)):
    p = grab(t, "sb_%02d.png"%i, 960)
    im = Image.open(p).convert("RGB").resize((TW, int(TW*9/16)), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    lab = "%05.2fs  镜%02d" % (t, sn)
    d.rectangle([0, im.height-34, TW, im.height], fill=(0,0,0,110))
    d.text((10, im.height-28), lab, font=F(19), fill=(255,255,255,235))
    tiles.append(im)
th = tiles[0].height
gap = 8
sheet = Image.new("RGB", (cols*TW+(cols-1)*gap, rows*th+(rows-1)*gap), (250,248,243))
for i,t in enumerate(tiles):
    r,c = divmod(i, cols)
    sheet.paste(t, (c*(TW+gap), r*(th+gap)))
sheet.save(os.path.join(OUT, "预览_分镜缩略图.jpg"), quality=88)
print("sheet", sheet.size)

# ---------- 封面 ----------
def cover(t, name, title_pos=(120, 700)):
    base = Image.open(grab(t, "cv_base_%d.png"%int(t*100))).convert("RGB")
    W,H = base.size
    # 底部渐变压暗
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        v = int(max(0, (y - H*0.45) / (H*0.55))**1.4 * 150)
        grad.putpixel((0,y), v)
    mask = grad.resize((W,H))
    dark = Image.new("RGB", (W,H), (8,10,8))
    img = Image.composite(dark, base, mask)
    d = ImageDraw.Draw(img)
    x,y = title_pos
    d.text((x, y), "一版秋花", font=F(104), fill=(250,247,240))
    d.line([x+4, y+150, x+4+150, y+150], fill=(240,236,228), width=2)
    d.text((x+6, y+172), "观澜 · 版画村   2026.11", font=F(30), fill=(232,228,220))
    img.save(os.path.join(OUT, name), quality=92)
    return img

c1 = cover(15.5, "_coverA.jpg")
print("done")
