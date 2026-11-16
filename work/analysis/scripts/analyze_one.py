# -*- coding: utf-8 -*-
"""Per-clip: extract 1fps frames (480w) + compute per-second image metrics + contact sheet."""
import os, sys, json, subprocess, time, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis"
FRAMES = os.path.join(OUT, "frames")
SHEETS = os.path.join(OUT, "sheets")
PARTS = os.path.join(OUT, "parts")

def stem_of(fn):
    return os.path.splitext(fn)[0]

def duration_of(path):
    import re
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        return None
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))

def extract(src, fdir, use_cuda=True, quiet=True):
    os.makedirs(fdir, exist_ok=True)
    pattern = os.path.join(fdir, "sec_%04d.jpg")
    base = [FF, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    if use_cuda:
        cmd = base + ["-hwaccel", "cuda", "-i", src, "-vf", "fps=1,scale=480:-2", "-q:v", "4", "-an", pattern]
    else:
        cmd = base + ["-i", src, "-vf", "fps=1,scale=480:-2", "-q:v", "4", "-an", pattern]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    dt = time.time() - t0
    n = len([f for f in os.listdir(fdir) if f.endswith(".jpg")])
    if p.returncode != 0 or n == 0:
        if not quiet:
            print("  cuda/run failed rc=%s n=%d err=%s" % (p.returncode, n, p.stderr.strip()[:300]), flush=True)
        return None if use_cuda else (n, dt, p.stderr)
    return (n, dt, p.stderr)

def lap_var(g):
    # 4-neighbour laplacian on float gray
    p = np.pad(g, 1, mode="edge")
    lap = p[:-2,1:-1] + p[2:,1:-1] + p[1:-1,:-2] + p[1:-1,2:] - 4.0*g
    return float(lap.var()), float(np.abs(lap).mean())

def sobel_stats(g):
    p = np.pad(g, 1, mode="edge")
    gx = (p[:-2,2:] + 2*p[1:-1,2:] + p[2:,2:]) - (p[:-2,:-2] + 2*p[1:-1,:-2] + p[2:,:-2])
    gy = (p[2:,:-2] + 2*p[2:,1:-1] + p[2:,2:]) - (p[:-2,:-2] + 2*p[:-2,1:-1] + p[:-2,2:])
    mag = np.sqrt(gx*gx + gy*gy)
    return float(mag.mean()), float(np.mean(mag > 30.0))

def entropy(g):
    h, _ = np.histogram(g, bins=64, range=(0.0, 255.0))
    p = h.astype(np.float64); s = p.sum()
    if s <= 0: return 0.0
    p = p / s
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())

def frame_metrics(path, prev_gray_small):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float32)
    R, G, B = a[:,:,0], a[:,:,1], a[:,:,2]
    gray = 0.299*R + 0.587*G + 0.114*B
    mx = a.max(axis=2); mn = a.min(axis=2)
    sat = float(np.mean((mx - mn) / (mx + 1.0)))
    rg = R - G
    yb = 0.5*(R + G) - B
    colorful = float(math.sqrt(rg.std()**2 + yb.std()**2) + 0.3*math.sqrt(rg.mean()**2 + yb.mean()**2))
    lv, lapabs = lap_var(gray)
    g2 = np.asarray(Image.fromarray(gray.astype(np.uint8)).resize((240, 135), Image.LANCZOS), dtype=np.float32)
    lv2, _ = lap_var(g2)
    fineratio = lv / max(4.0 * lv2, 1e-6)
    sm, edgefrac = sobel_stats(gray)
    warm = float(np.mean(((R - B) > 25) & ((R - G) > 10) & (R > 55)))
    med = float(np.median(gray))
    small = np.asarray(im.convert("L").resize((64, 36), Image.BILINEAR), dtype=np.float32)
    diff = 0.0
    if prev_gray_small is not None:
        diff = float(np.abs(small - prev_gray_small).mean())
    # local contrast: how much of the frame is flat (large dead areas = hand/lens cover)
    h, w = gray.shape
    bh, bw = h//3, w//4
    blocks = []
    for i in range(3):
        for j in range(4):
            blk = gray[i*bh:(i+1)*bh, j*bw:(j+1)*bw]
            blocks.append(float(blk.std()))
    flatfrac = float(np.mean([1.0 if b < 6.0 else 0.0 for b in blocks]))
    return {
        "luma": round(float(gray.mean()), 2),
        "lumastd": round(float(gray.std()), 2),
        "sharp": round(lv, 1),
        "lapabs": round(lapabs, 2),
        "grad": round(sm, 2),
        "edgefrac": round(edgefrac, 4),
        "fineratio": round(float(fineratio), 4),
        "warmfrac": round(warm, 4),
        "sat": round(sat, 4),
        "colorful": round(colorful, 2),
        "darkfrac": round(float(np.mean(gray < 28.0)), 4),
        "brightfrac": round(float(np.mean(gray > 230.0)), 4),
        "entropy": round(entropy(gray), 3),
        "uniform": round(float(np.mean(np.abs(gray - med) < 12.0)), 4),
        "flatfrac": round(flatfrac, 3),
        "diff": round(diff, 2),
        "_small": small,
    }

def make_sheet(stem, jpgs, cols=10, tw=192, maxtab=None):
    if not jpgs:
        return None, 0
    th = int(round(tw * 9.0 / 16.0))
    n = len(jpgs)
    rows = int(math.ceil(n / cols))
    W = cols * tw
    H = rows * th
    sheet = Image.new("RGB", (W, H), (24, 24, 24))
    try:
        font = ImageFont.load_default(size=13)
    except Exception:
        font = ImageFont.load_default()
    for i, jp in enumerate(jpgs):
        r, c = divmod(i, cols)
        try:
            t = Image.open(jp).convert("RGB").resize((tw, th), Image.BILINEAR)
        except Exception:
            continue
        sheet.paste(t, (c*tw, r*th))
        d = ImageDraw.Draw(sheet)
        lbl = str(i)
        bb = d.textbbox((0,0), lbl, font=font)
        d.rectangle([c*tw, r*th, c*tw + (bb[2]-bb[0]) + 6, r*th + (bb[3]-bb[1]) + 6], fill=(0,0,0))
        d.text((c*tw + 3, r*th + 1), lbl, fill=(255,230,80), font=font)
    p = os.path.join(SHEETS, stem + ".jpg")
    sheet.save(p, quality=82)
    return p, rows

def write_sheet_txt(stem, n, rows):
    with open(os.path.join(SHEETS, stem + ".txt"), "w", encoding="utf-8") as fh:
        fh.write("sheet: %s.jpg  grid=10 cols x %d rows, cell=192x108px\n" % (stem, rows))
        fh.write("t (seconds) = row*10 + col (0-based). frame file = frames/%s/sec_%%04d.jpg (1-based index = t+1)\n" % stem)
        fh.write("cell label = t in seconds\n\n")
        for i in range(n):
            r, c = divmod(i, 10)
            fh.write("row %d col %d -> t=%d s (= %d:%02d)  sec_%04d.jpg\n" % (r, c, i, i//60, i%60, i+1))

def metrics_only(fn):
    """Recompute metrics from frames already on disk (no decode). Regenerates sheet + txt + part json."""
    src = os.path.join(SRC, fn); stem = stem_of(fn)
    fdir = os.path.join(FRAMES, stem)
    if not os.path.isdir(fdir):
        raise RuntimeError("no frames dir: " + stem)
    jpgs = sorted(f for f in os.listdir(fdir) if f.endswith(".jpg"))
    if not jpgs:
        raise RuntimeError("no frames: " + stem)
    dur = duration_of(src)
    t0 = time.time()
    frames = []; prev = None
    for i, jf in enumerate(jpgs):
        m = frame_metrics(os.path.join(fdir, jf), prev)
        prev = m.pop("_small")
        frames.append({"t": i, **m})
    sheet, rows = make_sheet(stem, [os.path.join(fdir, j) for j in jpgs])
    write_sheet_txt(stem, len(jpgs), rows)
    out = {"file": fn, "stem": stem, "duration": round(dur, 2) if dur else None,
           "n_frames": len(frames), "sheet": os.path.basename(sheet) if sheet else None,
           "rows": rows, "elapsed": round(time.time()-t0, 1), "frames": frames}
    with open(os.path.join(PARTS, stem + ".json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return out

def analyze(fn, use_cuda=True, force=False):
    src = os.path.join(SRC, fn)
    stem = stem_of(fn)
    fdir = os.path.join(FRAMES, stem)
    dur = duration_of(src)
    t0 = time.time()
    need = max(1, int(round(dur))) if dur else None
    have = len([f for f in os.listdir(fdir) if f.endswith(".jpg")]) if os.path.isdir(fdir) else 0
    if force or need is None or have < need - 1:
        res = extract(src, fdir, use_cuda=True)
        if res is None:
            if os.path.isdir(fdir):
                for f in os.listdir(fdir):
                    try: os.remove(os.path.join(fdir, f))
                    except Exception: pass
            res = extract(src, fdir, use_cuda=False)
        if res is None:
            raise RuntimeError("extraction failed both ways: " + fn)
    jpgs = sorted(f for f in os.listdir(fdir) if f.endswith(".jpg"))
    frames = []
    prev = None
    for i, jf in enumerate(jpgs):
        m = frame_metrics(os.path.join(fdir, jf), prev)
        prev = m.pop("_small")
        m = {"t": i, **m}
        frames.append(m)
    sheet, rows = make_sheet(stem, [os.path.join(fdir, j) for j in jpgs])
    write_sheet_txt(stem, len(jpgs), rows)
    out = {"file": fn, "stem": stem, "duration": round(dur, 2) if dur else None,
           "n_frames": len(frames), "sheet": os.path.basename(sheet) if sheet else None,
           "rows": rows, "elapsed": round(time.time()-t0, 1), "frames": frames}
    with open(os.path.join(PARTS, stem + ".json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return out

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--nocuda", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--metrics-only", action="store_true")
    a = ap.parse_args()
    for fn in a.files:
        try:
            if a.metrics_only:
                o = metrics_only(fn)
            else:
                o = analyze(fn, use_cuda=not a.nocuda, force=a.force)
            print("OK %-18s frames=%d dur=%s rows=%s %.1fs" % (fn, o["n_frames"], o["duration"], o["rows"], o["elapsed"]), flush=True)
        except Exception as e:
            print("FAIL %s %r" % (fn, e), flush=True)