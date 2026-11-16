# -*- coding: utf-8 -*-
"""Per-clip: 2fps frame extraction (480w) + per-frame metrics + dup-detection hashes."""
import os, sys, json, subprocess, time, math
import numpy as np
from PIL import Image

OLD = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\scripts"
sys.path.insert(0, OLD)
from analyze_one import frame_metrics, lap_var, sobel_stats, entropy, duration_of

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
FRAMES = os.path.join(OUT, "frames")
PARTS = os.path.join(OUT, "parts")
HASHES = os.path.join(OUT, "hashes")

def stem_of(fn):
    return os.path.splitext(fn)[0]

def extract(src, fdir, use_cuda=True):
    os.makedirs(fdir, exist_ok=True)
    pattern = os.path.join(fdir, "sec_%04d.jpg")
    for f in os.listdir(fdir):
        if f.endswith(".jpg"):
            try: os.remove(os.path.join(fdir, f))
            except Exception: pass
    pre = [FF, "-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
    vf = "fps=2,scale=480:-2"
    cmd = (pre + (["-hwaccel", "cuda"] if use_cuda else []) + ["-i", src, "-vf", vf, "-q:v", "4", "-an", pattern])
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    n = len([f for f in os.listdir(fdir) if f.endswith(".jpg")])
    if p.returncode != 0 or n == 0:
        return None if use_cuda else (n, time.time()-t0, p.stderr)
    return (n, time.time()-t0, p.stderr)

def bits_to_int(b):
    v = 0
    for x in b:
        v = (v << 1) | int(x)
    return v

def hashes_of(im):
    g = im.convert("L")
    a = np.asarray(g.resize((9, 8), Image.BILINEAR), dtype=np.int16)
    dhash = bits_to_int((a[:, 1:] > a[:, :-1]).flatten())
    b8 = np.asarray(g.resize((8, 8), Image.BILINEAR), dtype=np.float32)
    ahash = bits_to_int((b8.flatten() > b8.mean()).flatten())
    hsv = np.asarray(im.convert("HSV"), dtype=np.float32)
    H, S, V = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
    w = (S/255.0) * (V/255.0)
    hh = np.histogram(H, bins=12, range=(0, 256), weights=w)[0]
    ss = np.histogram(S, bins=4, range=(0, 256))[0].astype(np.float32)
    vv = np.histogram(V, bins=8, range=(0, 256))[0].astype(np.float32)
    hh = hh / max(hh.sum(), 1e-6); ss = ss / max(ss.sum(), 1e-6); vv = vv / max(vv.sum(), 1e-6)
    hist = np.concatenate([hh, ss, vv]).tolist()
    # composition fractions
    r = np.asarray(im.convert("RGB"), dtype=np.float32)
    R, G, B = r[:,:,0], r[:,:,1], r[:,:,2]
    mx = r.max(axis=2); mn = r.min(axis=2)
    delta = np.maximum(mx - mn, 1e-6)
    hue = np.zeros_like(mx)
    m = (mx == R); hue[m] = ((G[m]-B[m])/delta[m]) % 6.0
    m = (mx == G) & (mx != R); hue[m] = ((B[m]-R[m])/delta[m]) + 2.0
    m = (mx == B) & (mx != R) & (mx != G); hue[m] = ((R[m]-G[m])/delta[m]) + 4.0
    hue = hue / 6.0
    satn = delta / np.maximum(mx, 1e-6)
    sky = float(np.mean((hue > 0.50) & (hue < 0.72) & (satn > 0.12) & (mx > 110)))
    green = float(np.mean((hue > 0.20) & (hue < 0.45) & (satn > 0.15) & (mx > 40)))
    warm = float(np.mean(((R - B) > 25) & ((R - G) > 10) & (R > 55)))
    return dhash, ahash, hist, sky, green, warm

def analyze(fn, force=False):
    src = os.path.join(SRC, fn)
    stem = stem_of(fn)
    fdir = os.path.join(FRAMES, stem)
    dur = duration_of(src)
    t0 = time.time()
    need = max(1, int(round(dur * 2))) if dur else None
    have = len([f for f in os.listdir(fdir) if f.endswith(".jpg")]) if os.path.isdir(fdir) else 0
    if force or need is None or have < need - 1 or have == 0:
        res = extract(src, fdir, True)
        if res is None:
            res = extract(src, fdir, False)
        if res is None:
            raise RuntimeError("extract failed: " + fn)
    jpgs = sorted(f for f in os.listdir(fdir) if f.endswith(".jpg"))
    frames = []; hs = []
    prev = None
    for i, jf in enumerate(jpgs):
        im = Image.open(os.path.join(fdir, jf)).convert("RGB")
        m = frame_metrics(os.path.join(fdir, jf), prev)
        prev = m.pop("_small")
        t = round(i * 0.5, 2)
        frames.append({"t": t, **m})
        dh, ah, hist, sky, green, warm = hashes_of(im)
        hs.append({"t": t, "dhash": dh, "ahash": ah, "hist": [round(x, 5) for x in hist],
                   "sky": round(sky, 4), "green": round(green, 4), "warm": round(warm, 4)})
    out = {"file": fn, "stem": stem, "duration": round(dur, 3) if dur else None,
           "n_frames": len(frames), "fps_samples": 2, "elapsed": round(time.time()-t0, 2), "frames": frames}
    with open(os.path.join(PARTS, stem + ".json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    with open(os.path.join(HASHES, stem + ".json"), "w", encoding="utf-8") as fh:
        json.dump({"file": fn, "stem": stem, "duration": out["duration"], "frames": hs}, fh, ensure_ascii=False)
    return out

if __name__ == "__main__":
    for fn in sys.argv[1:]:
        try:
            o = analyze(fn)
            print("OK %-16s frames=%2d dur=%.2f %.1fs" % (fn, o["n_frames"], o["duration"], o["elapsed"]), flush=True)
        except Exception as e:
            print("FAIL %s %r" % (fn, e), flush=True)
