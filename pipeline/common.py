# -*- coding: utf-8 -*-
"""openfilm pipeline shared helpers."""
import json, os, re, subprocess, sys
import numpy as np, cv2

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
PIPE = os.path.join(ROOT, "pipeline")
RULES = json.load(open(os.path.join(PIPE, "rules.json"), encoding="utf-8"))
_CASCADE = None

def imread_u(p):
    try: return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception: return None

def probe(path):
    s = subprocess.run([FF, "-hide_banner", "-i", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stderr.decode("utf-8", "replace")
    d = {"file": os.path.basename(path)}
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", s)
    if m: d["dur"] = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    m = re.search(r"Video: \w+.*?, (\d+)x(\d+)", s)
    if m: d["w"] = int(m.group(1)); d["h"] = int(m.group(2))
    m = re.search(r"rotation of ([\-\d.]+) degrees", s)
    d["rot"] = float(m.group(1)) if m else 0.0
    m = re.search(r"timecode\s+:\s+(\d+):(\d+):(\d+):(\d+)", s)
    if m: d["tc"] = d["tc_sec"] = int(m.group(1))*3600+int(m.group(2))*60+int(m.group(3))+int(m.group(4))/50.0
    d["tc"] = d.get("tc", "-")
    return d

def aspect_class(d):
    rot = abs(d.get("rot", 0)) % 180
    if rot in (90, 270): return "portrait-rotated"
    if d.get("w", 0) > d.get("h", 0): return "landscape"
    return "portrait"

def extract_frames(src, outdir, fps=2, width=480):
    os.makedirs(outdir, exist_ok=True)
    if len(os.listdir(outdir)) >= 4: return len(os.listdir(outdir))
    subprocess.run([FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-i", src,
                    "-vf", "fps=%d,scale=%d:-2" % (fps, width), "-q:v", "3",
                    os.path.join(outdir, "%03d.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return len(os.listdir(outdir))

def faces(img):
    global _CASCADE
    if _CASCADE is None:
        _CASCADE = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.equalizeHist(g)
    f = _CASCADE.detectMultiScale(g, 1.1, 5, minSize=(28, 28))
    return len(f), (max([w*h for (_, _, w, h) in f]) / float(g.size) if len(f) else 0.0)

def frame_stats(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lap = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    hist = cv2.calcHist([hsv], [0, 1], None, [12, 8], [0, 180, 0, 256]).ravel()
    hist = hist / (hist.sum() + 1e-9)
    return dict(sharp=float(lap.var()), bright=float(g.mean()), sat=float(hsv[..., 1].mean()),
                edge=float(cv2.Canny(g.astype(np.uint8), 80, 160).mean()/255.0), hist=hist)

def quality_score(rows):
    if not rows: return 0.0
    sh = float(np.median([r["sharp"] for r in rows]))
    br = float(np.median([r["bright"] for r in rows]))
    fc = float(np.mean([r.get("faces", 0) for r in rows]))
    edge = float(np.median([r["edge"] for r in rows]))
    pen = max(0.0, br-228)*0.9 + max(0.0, 70-br)*0.6
    return sh/1000.0 + fc*1.5 + edge*8.0 - pen

def hist_dist(a, b):
    return float(np.abs(np.asarray(a) - np.asarray(b)).sum())

def best_window(rows, dur_src, step=0.5):
    """Sliding window over per-0.5s rows; maximise median sharpness, avoid blown highlights."""
    n = max(1, int(round(dur_src/step)))
    best, bs = -1e9, 0.0
    for i in range(0, max(1, len(rows)-n+1)):
        sel = rows[i:i+n]
        if not sel: break
        sh = np.median([r["sharp"] for r in sel]); br = np.median([r["bright"] for r in sel])
        s = sh - max(0.0, 235-br)*60 - max(0.0, 65-br)*40
        if s > best: best, bs = s, i*step
    return bs, best

def mmss(x): return "%d:%05.2f" % (int(x//60), x % 60)

def pos_gap(edl, a, b):
    pos = edl.get("pos") or []
    if a < len(pos) and b < len(pos): return abs(pos[a] - pos[b])
    return 1e9
