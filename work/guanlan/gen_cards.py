
# -*- coding: utf-8 -*-
import os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\gfx"
os.makedirs(OUT, exist_ok=True)
SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
SERIF_SEMI = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
HEAVY = r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"
PAPER = (246, 241, 231); INK = (38, 36, 31); GRAY = (132, 125, 111); SEAL = (170, 56, 44)
F = lambda p, s: ImageFont.truetype(p, s)

def paper_base(seed=7):
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(26):
        x, y = rnd.randint(-200, W+200), rnd.randint(-150, H+150)
        r = rnd.randint(140, 430)
        d.ellipse([x-r, y-r*0.7, x+r, y+r*0.7], fill=(208, 196, 174, rnd.randint(3, 8)))
    for _ in range(800):
        x, y = rnd.randint(0, W), rnd.randint(0, H)
        ln = rnd.randint(6, 40); ang = rnd.uniform(-0.2, 0.2)
        d.line([x, y, x + ln*rnd.choice([-1, 1]), y + ln*ang], fill=(198, 188, 166, rnd.randint(4, 11)), width=1)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    a = np.array(img, dtype=np.int16)
    n = np.random.default_rng(seed).normal(0, 3.0, (H, W, 1)).repeat(3, axis=2)
    return Image.fromarray(np.clip(a + n.astype(np.int16), 0, 255).astype(np.uint8))

def tracked(d, x, y, text, fnt, fill, tracking=0.0, word_gap=0.0):
    for ch in text:
        if ch == " ":
            x += d.textlength(" ", font=fnt) + tracking + word_gap
            continue
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + tracking
    return x

def tracked_w(d, text, fnt, tracking=0.0, word_gap=0.0):
    return sum((d.textlength(" ", font=fnt) + tracking + word_gap) if c == " " else (d.textlength(c, font=fnt) + tracking) for c in text) - tracking

def seal(img, x, y, size, chars, fs):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x+size, y+size], radius=max(3, size//18), fill=SEAL)
    p = max(2, size//26)
    d.rectangle([x+p, y+p, x+size-p, y+size-p], outline=PAPER, width=max(2, size//34))
    f = F(HEAVY, fs)
    n = len(chars)
    gap = (size - 2*p - fs*n) / (n + 1)
    for i, ch in enumerate(chars):
        w = d.textlength(ch, font=f)
        d.text((x + (size-w)/2, y + p + gap*(i+1) + fs*i - fs*0.12), ch, font=f, fill=PAPER)
    return d

def make_open():
    img = paper_base(3); d = ImageDraw.Draw(img)
    f_place = F(SERIF, 30); f_title = F(SERIF, 172); f_en = F(SERIF, 23)
    x0 = 236
    tracked(d, x0+2, 322, "观澜 · 版画村", f_place, GRAY, 5)
    d.text((x0-8, 396), "一版秋花", font=f_title, fill=INK)
    d.line([x0, 700, x0+296, 700], fill=(158, 150, 134), width=2)
    tracked(d, x0+1, 728, "A PRINT OF AUTUMN", f_en, GRAY, 6.5, 4.0)
    # 小印章 右上
    seal(img, 1478, 452, 76, "秋", 40)
    return img

def make_end():
    img = paper_base(11); d = ImageDraw.Draw(img)
    f_t = F(SERIF, 58); f_l = F(SERIF, 48); f_s = F(SERIF, 26)
    cx = W//2
    t = "一版秋花"; tw = tracked_w(d, t, f_t, 12)
    tracked(d, cx-tw/2, 352, t, f_t, INK, 12)
    line = "把秋天，套一次色"; lw = tracked_w(d, line, f_l, 10)
    tracked(d, cx-lw/2, 462, line, f_l, (56, 52, 44), 10)
    d.line([cx-118, 596, cx+118, 596], fill=(160, 152, 136), width=2)
    sub = "深圳 · 观澜版画村"; sw = tracked_w(d, sub, f_s, 4)
    tracked(d, cx-sw/2-60, 644, sub, f_s, GRAY, 4)
    dt = "2026.11"; dw = tracked_w(d, dt, f_s, 4)
    tracked(d, cx+96, 644, dt, f_s, GRAY, 4)
    seal(img, cx + 268, 630, 100, "观澜", 33)
    return img

make_open().save(os.path.join(OUT, "card_open.png"))
make_end().save(os.path.join(OUT, "card_end.png"))
print("ok")
