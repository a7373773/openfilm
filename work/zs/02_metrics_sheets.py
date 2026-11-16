# -*- coding: utf-8 -*-
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs")
FR   = os.path.join(WORK, "frames")
SH   = os.path.join(WORK, "sheets"); os.makedirs(SH, exist_ok=True)
meta = json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))
meta.sort(key=lambda d: d.get("tc_sec", 0))

def imread_u(path):
    try:
        buf = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(buf, cv2.IMREAD_COLOR)
    except Exception:
        return None

def metrics(path):
    img = imread_u(path)
    if img is None: return None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    edges = cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 80, 160).mean()/255.0
    hist = cv2.calcHist([g], [0], None, [64], [0, 256]).ravel(); hist /= hist.sum()+1e-9
    ent = float(-(hist[hist>0]*np.log2(hist[hist>0])).sum())
    # region brightness: top third (sky-ish) vs bottom third (ground-ish)
    hh = g.shape[0]//3
    top = float(g[:hh].mean()); bot = float(g[2*hh:].mean()); mid = float(g[hh:2*hh].mean())
    return dict(sharp=float(lap.var()), edge=float(edges), bright=float(g.mean()),
                sat=float(hsv[...,1].mean()), hue=float(hsv[...,0].mean()),
                ent=ent, top=top, bot=bot, mid=mid,
                white=float((g>250).mean()), black=float((g<12).mean()))

def filmstrip(clip):
    d = os.path.join(FR, os.path.splitext(clip)[0])
    return sorted(os.path.join(d, f) for f in os.listdir(d)) if os.path.isdir(d) else []

allm = {}
for m in meta:
    rows = []
    for p in filmstrip(m["file"]):
        r = metrics(p)
        if r: r["t"] = os.path.basename(p).replace(".jpg",""); rows.append(r)
    allm[m["file"]] = rows
json.dump(allm, open(os.path.join(WORK, "metrics.json"), "w", encoding="utf-8"), indent=0)

# per-clip summary
summ = []
for m in meta:
    rows = allm[m["file"]]
    if not rows: continue
    n = len(rows)
    sel = rows[len(rows)//6 : max(len(rows)//6+1, len(rows)*5//6)] or rows  # drop first/last 1/6
    sh = np.median([r["sharp"] for r in sel])
    best = max(sel, key=lambda r: r["sharp"])
    summ.append(dict(file=m["file"], tc=m.get("tc"), dur=m.get("dur"), n=n,
        sharp=round(float(sh),1), best_t=best["t"], best_sharp=round(best["sharp"],1),
        bright=round(float(np.median([r["bright"] for r in sel])),1),
        sat=round(float(np.median([r["sat"] for r in sel])),1), edge=round(float(np.median([r["edge"] for r in sel])),3)))
json.dump(summ, open(os.path.join(WORK, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("clips", len(summ), "frames", sum(len(v) for v in allm.values()))
sh = sorted(s["sharp"] for s in summ)
print("sharp p10/p50/p90", sh[len(sh)//10], sh[len(sh)//2], sh[9*len(sh)//10])

# ---------- overview sheets: 1 tile per clip ----------
FONT = None
for fp in [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arial.ttf"]:
    if os.path.exists(fp): FONT = ImageFont.truetype(fp, 20); break
if FONT is None: FONT = ImageFont.load_default()

TW, TH = 426, 240
COLS, ROWS = 4, 5
PER = COLS*ROWS
sheets = []
for si in range(0, len(summ), PER):
    chunk = summ[si:si+PER]
    sheet = Image.new("RGB", (COLS*TW, ROWS*(TH+30)), (16,16,16))
    dr = ImageDraw.Draw(sheet)
    for k, s in enumerate(chunk):
        cx, cy = (k % COLS)*TW, (k // COLS)*(TH+30)
        p = os.path.join(FR, os.path.splitext(s["file"])[0], s["best_t"]+".jpg")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB").resize((TW, TH))
            sheet.paste(im, (cx, cy))
        lbl = "#%02d %s %s sh%.0f" % (si+k+1, s["file"], (s.get("tc") or "")[:8], s["sharp"])
        dr.text((cx+6, cy+TH+4), lbl, fill=(235,235,235), font=FONT)
    out = os.path.join(SH, "overview_%02d.jpg" % (si//PER+1))
    sheet.save(out, quality=88)
    sheets.append(os.path.basename(out))
json.dump(summ, open(os.path.join(WORK, "clips_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("sheets", sheets)