
# -*- coding: utf-8 -*-
"""Generate title / lower-third / sticker / end-card overlays (1920x1080 RGBA PNGs)."""
import os, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\graphics"
os.makedirs(OUT, exist_ok=True)
F_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
F_REG  = r"C:\Windows\Fonts\msyh.ttc"
F_LIGHT = r"C:\Windows\Fonts\msyhl.ttc"
ORANGE = (255, 122, 61)
GREEN = (126, 217, 87)
WHITE = (255, 255, 255)

def font(path, size):
    return ImageFont.truetype(path, size)

def text_size(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]

def shadowed(d, xy, s, f, fill, alpha=255, shadow=(0, 0, 0, 150), off=3, blur_img=None):
    x, y = xy
    d.text((x + off, y + off), s, font=f, fill=shadow)
    d.text((x, y), s, font=f, fill=fill + (alpha,) if len(fill) == 3 else fill)

def letterbox_scrim(size, x0, y0, x1, y1, a0=0, a1=150):
    """left-to-right dark gradient for legibility"""
    g = Image.new("L", (x1 - x0, y1 - y0), 0)
    gd = ImageDraw.Draw(g)
    for i in range(x1 - x0):
        gd.line([(i, 0), (i, y1 - y0)], fill=int(a0 + (a1 - a0) * (i / max(1, (x1 - x0 - 1)))))
    return g

def canvas():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p)
    return p

# ---------------- 1. TITLE ----------------
im = canvas()
# bottom scrim
scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(scrim)
for y in range(H):
    k = max(0.0, (y - H * 0.45) / (H * 0.55))
    sd.line([(0, y), (W, y)], fill=(0, 0, 0, int(120 * k ** 1.6)))
im = Image.alpha_composite(im, scrim)
# left vertical gradient (subtle)
lg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ld = ImageDraw.Draw(lg)
for x in range(int(W * 0.62)):
    ld.line([(x, 0), (x, H)], fill=(0, 0, 0, int(105 * (1 - x / (W * 0.62)) ** 1.5)))
im = Image.alpha_composite(im, lg)
d = ImageDraw.Draw(im)
f_kicker = font(F_REG, 32); f_title = font(F_BOLD, 118); f_sub = font(F_LIGHT, 40)
x, y = 150, 360
d.text((x, y), "运动 · 健康 · 山野", font=f_kicker, fill=(255, 255, 255, 215))
d.line([(x, y + 56), (x + 74, y + 56)], fill=ORANGE + (255,), width=5)
ty = y + 92
d.text((x + 4, ty + 4), "山野之间", font=f_title, fill=(0, 0, 0, 130))
d.text((x, ty), "山野之间", font=f_title, fill=(255, 255, 255, 255))
d.text((x + 4, ty + 168), "一场关于呼吸与坚持的徒步", font=f_sub, fill=(0, 0, 0, 120))
d.text((x, ty + 164), "一场关于呼吸与坚持的徒步", font=f_sub, fill=(255, 255, 255, 232))
p_title = save(im, "01_title.png")

# ---------------- 2. LOWER THIRDS ----------------
LT = [
    ("出发", "把城市的噪音留在身后"),
    ("身体先醒过来", "心率加快，呼吸变深"),
    ("林间穿行", "找到自己的节奏"),
    ("最陡的一段", "慢一点也没关系"),
    ("补给时刻", "水 · 盐分 · 一点耐心"),
    ("山脊之上", "云在脚下，风在耳边"),
    ("登顶", "坚持的人，风景会自己找上来"),
]
lt_paths = []
for i, (main, sub) in enumerate(LT):
    im = canvas()
    d = ImageDraw.Draw(im)
    f_m = font(F_BOLD, 46); f_s = font(F_REG, 30)
    x, y = 132, 902
    # plate
    w_main = text_size(d, main, f_m)[0]
    w_sub = text_size(d, sub, f_s)[0]
    pw = max(w_main, w_sub) + 86
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle([x - 26, y - 26, x + pw, y + 96], radius=18, fill=(10, 12, 14, 118))
    im = Image.alpha_composite(im, plate)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x - 26, y - 26, x - 20, y + 96], radius=3, fill=ORANGE + (255,))
    d.text((x + 2, y - 10), main, font=f_m, fill=(255, 255, 255, 250))
    d.text((x, y + 50), sub, font=f_s, fill=(255, 255, 255, 205))
    lt_paths.append(save(im, "lt_%02d.png" % (i + 1)))

# ---------------- 3. STICKERS ----------------
def sticker_base(size=132, radius=34, alpha=112):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    return im, d

def draw_sun(d, cx, cy, s=1.0):
    r = int(26 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE + (255,))
    import math
    for k in range(8):
        a = k * math.pi / 4
        x0 = cx + int(math.cos(a) * (r + 12)); y0 = cy + int(math.sin(a) * (r + 12))
        x1 = cx + int(math.cos(a) * (r + 26)); y1 = cy + int(math.sin(a) * (r + 26))
        d.line([(x0, y0), (x1, y1)], fill=(255, 255, 255, 240), width=max(2, int(4 * s)))

def draw_heart_ecg(d, cx, cy, s=1.0):
    pts = [(-46, 4), (-28, 4), (-18, -22), (-6, 26), (6, -10), (18, 4), (46, 4)]
    pts = [(cx + int(px * s), cy + int(py * s)) for px, py in pts]
    d.line(pts, fill=(255, 255, 255, 245), width=max(3, int(5 * s)), joint="curve")
    # small heart
    hx, hy = cx - 44, cy - 26
    d.polygon([(hx, hy + 8), (hx + 9, hy - 4), (hx + 18, hy + 8)], fill=ORANGE + (255,))

def draw_drop(d, cx, cy, s=1.0):
    d.polygon([(cx, cy - 34), (cx + 20, cy + 4), (cx, cy + 26), (cx - 20, cy + 4)],
              fill=(120, 200, 255, 250))
    d.ellipse([cx - 8, cy - 2, cx + 2, cy + 10], fill=(255, 255, 255, 190))

def draw_boot(d, cx, cy, s=1.0):
    d.rounded_rectangle([cx - 34, cy - 18, cx + 6, cy + 12], radius=8, fill=(255, 255, 255, 245))
    d.rounded_rectangle([cx - 4, cy + 4, cx + 34, cy + 20], radius=7, fill=(255, 255, 255, 245))
    d.line([(cx - 34, cy + 16), (cx + 30, cy + 24)], fill=ORANGE + (255,), width=5)

def draw_flag(d, cx, cy, s=1.0):
    d.line([(cx - 22, cy + 34), (cx - 22, cy - 38)], fill=(255, 255, 255, 245), width=6)
    d.polygon([(cx - 18, cy - 36), (cx + 34, cy - 22), (cx - 18, cy - 6)], fill=ORANGE + (255,))
    d.ellipse([cx - 32, cy + 30, cx - 12, cy + 42], fill=(255, 255, 255, 235))

stickers = [
    ("03_st_sun.png", draw_sun, 1560, 190),
    ("04_st_heart.png", draw_heart_ecg, 1730, 300),
    ("05_st_water.png", draw_drop, 1700, 250),
    ("06_st_boot.png", draw_boot, 1600, 260),
    ("07_st_flag.png", draw_flag, 1650, 220),
]
st_paths = []
for name, fn, cx, cy in stickers:
    im = canvas()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([cx - 78, cy - 78, cx + 78, cy + 78], radius=40, fill=(12, 14, 16, 108))
    d.rounded_rectangle([cx - 78, cy - 78, cx + 78, cy + 78], radius=40, outline=(255, 255, 255, 55), width=2)
    fn(d, cx, cy, 1.0)
    st_paths.append(save(im, name))

# ---------------- 4. END CARD ----------------
im = canvas()
d = ImageDraw.Draw(im)
d.rectangle([0, 0, W, H], fill=(0, 0, 0, 150))
f_big = font(F_BOLD, 84); f_mid = font(F_REG, 40); f_small = font(F_LIGHT, 24)
t1 = "运动 · 健康 · 山野"
w1 = text_size(d, t1, f_big)[0]
d.text(((W - w1) // 2 + 3, 404), t1, font=f_big, fill=(0, 0, 0, 140))
d.text(((W - w1) // 2, 400), t1, font=f_big, fill=(255, 255, 255, 250))
d.line([((W - 90) // 2, 528), ((W + 90) // 2, 528)], fill=ORANGE + (255,), width=4)
t2 = "今天流的汗，是明天的底气"
w2 = text_size(d, t2, f_mid)[0]
d.text(((W - w2) // 2, 578), t2, font=f_mid, fill=(255, 255, 255, 226))
t3 = "音乐：Life of Riley — Kevin MacLeod (incompetech.com) · CC BY 4.0"
w3 = text_size(d, t3, f_small)[0]
d.text(((W - w3) // 2, 940), t3, font=f_small, fill=(255, 255, 255, 150))
p_end = save(im, "08_endcard.png")

# ---------------- 5. PROGRESS BAR ----------------
bar_bg = canvas(); d = ImageDraw.Draw(bar_bg)
d.rounded_rectangle([120, 1042, 1800, 1052], radius=5, fill=(255, 255, 255, 70))
p_barbg = save(bar_bg, "09_bar_bg.png")
bar_fill = canvas(); d = ImageDraw.Draw(bar_fill)
d.rounded_rectangle([120, 1042, 1800, 1052], radius=5, fill=ORANGE + (235,))
p_barfill = save(bar_fill, "10_bar_fill.png")

print("generated", len(os.listdir(OUT)), "files")
for f in sorted(os.listdir(OUT)): print(" ", f)
