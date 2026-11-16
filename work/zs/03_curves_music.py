# -*- coding: utf-8 -*-
import json, os, subprocess, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs")
MUS = os.path.join(ROOT, "work", "music", "src")

print("=== CLIP CURVES (sharp per 0.5s step, x1000) ===")
m = json.load(open(os.path.join(WORK, "metrics.json"), encoding="utf-8"))
meta = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
for f in sorted(m):
    rows = m[f]
    if not rows: continue
    sh = [int(r["sharp"]/1000) for r in rows]
    br = [int(r["bright"]) for r in rows]
    print("%s d=%.1f sh=%s br=%s" % (f, meta[f].get("dur", 0), ",".join(str(x) for x in sh), ",".join(str(x) for x in br)))

print("\n=== MUSIC ===")
for name in ["Carefree.mp3", "Cattails.mp3", "Life of Riley.mp3", "Open Those Bright Eyes.mp3", "Sapphire Isle.mp3", "Wallpaper.mp3"]:
    p = os.path.join(MUS, name)
    if not os.path.exists(p): continue
    raw = subprocess.run([FF, "-v", "error", "-i", p, "-t", "260", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         stdout=subprocess.PIPE).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32)/32768.0
    dur = len(a)/16000.0
    bar = 2.5  # 96bpm
    nb = int(dur/bar)
    rms = [float(np.sqrt(np.mean(a[int(i*bar*16000):int((i+1)*bar*16000)]**2))) for i in range(nb)]
    db = [int(20*np.log10(max(r, 1e-6))) for r in rms]
    print("%s dur~%.1fs bars=%d" % (name, dur, nb))
    print("  rms_db:", ",".join(str(x) for x in db))
