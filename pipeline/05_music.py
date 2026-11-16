# -*- coding: utf-8 -*-
"""05_music: pick a BGM that matches theme + scene. Light, upbeat, steady energy."""
import json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RULES, FF

MDIR = sys.argv[1] if len(sys.argv) > 1 else r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\music\src"
TARGET = float(sys.argv[2]) if len(sys.argv) > 2 else 130.0
SR = 16000

def decode(p, secs=90):
    raw = subprocess.run([FF, "-v", "error", "-i", p, "-t", str(secs), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

def full_dur(p):
    s = subprocess.run([FF, "-hide_banner", "-i", p], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stderr.decode("utf-8", "replace")
    import re
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", s)
    return int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3)) if m else 0

def analyse(p):
    a = decode(p)
    hop, win = 160, 512
    n = (len(a) - win) // hop
    if n < 10: return None
    fr = np.lib.stride_tricks.as_strided(a, (n, win), (a.strides[0]*hop, a.strides[0]))
    energy = (fr**2).sum(1)
    flux = np.maximum(0, np.diff(np.log1p(energy*1e4)))
    # tempo from onset autocorrelation
    f = flux - flux.mean()
    ac = np.correlate(f, f, "full")[len(f)-1:]
    lo, hi = int(100*60/200), int(100*60/50)
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60.0*100/lag
    while bpm < 70: bpm *= 2          # fold octave ambiguity into 70-140
    while bpm > 140: bpm /= 2
    # energy steadiness per 2.5s bar
    bar = int(2.5*SR); nb = len(a)//bar
    rms = np.array([20*np.log10(np.sqrt(np.mean(a[i*bar:(i+1)*bar]**2))+1e-9) for i in range(nb)])
    swing = float(np.percentile(rms, 90) - np.percentile(rms, 10))
    # spectral centroid + low-band ratio
    # onset density (notes per second) = how "jumpy" the piece is
    fl = flux[flux > flux.mean() + flux.std()*0.6]
    onset_ps = float(len(fl) / (len(a)/SR))
    spec = np.abs(np.fft.rfft(a[:SR*20] * np.hanning(min(len(a), SR*20))))
    freqs = np.fft.rfftfreq(min(len(a), SR*20), 1.0/SR)
    cent = float((spec*freqs).sum()/max(1e-9, spec.sum()))
    low = float(spec[freqs < 150].sum()/max(1e-9, spec.sum()))
    return dict(bpm=round(bpm, 1), swing=round(swing, 2), centroid=round(cent, 0), low=round(low, 3),
                onset=round(onset_ps, 2), mean_db=round(float(np.mean(rms)), 1))

files = sorted(f for f in os.listdir(MDIR) if f.lower().endswith((".mp3", ".wav", ".m4a", ".flac")))
rows = []
for f in files:
    info = analyse(os.path.join(MDIR, f))
    if not info: continue
    d = full_dur(os.path.join(MDIR, f))
    info.update(file=f, dur=round(d, 1))
    rules = RULES["music"]
    bpm_ok = rules["bpm_range"][0] <= info["bpm"] <= rules["bpm_range"][1]
    steady = info["swing"] <= rules["rms_swing_max_db"]
    prof = sys.argv[3] if len(sys.argv) > 3 else "bright"
    if prof == "calm":
        # 舒缓：慢、稀疏、暗、轻、平稳
        s = 0.0
        s += max(0.0, 30 - max(0.0, info["bpm"] - 82)*1.6 - max(0.0, 62 - info["bpm"])*1.2)
        s += max(0.0, 25 - info["onset"]*9.0)
        s += 20 - min(20, max(0.0, info["centroid"] - 1100)/140)
        s += 15 - min(15, abs(info["mean_db"] + 20)*1.5)
        s += 10 - min(10, info["swing"]*1.2)
    else:
        s = 0.0
        s += max(0.0, 30 - abs(info["bpm"] - 96)*0.9)
        s += max(0.0, 25 - info["swing"]*2.2)
        s += 20 - min(20, abs(info["centroid"] - 1600)/120)
        s += 25 - min(25, info["low"]*120)
        if not steady: s -= 10
    if not bpm_ok: s -= 12
    if info["dur"] < TARGET*0.95: s -= 8
    bl = RULES["music"].get("blacklist", {})
    if f in bl:
        info["score"] = -100.0; info["excluded"] = bl[f]
    else:
        info["score"] = round(s, 1)
    rows.append(info)

rows.sort(key=lambda r: -r["score"])
print("BGM candidates for %.0fs cut (light / upbeat / steady):\n" % TARGET)
print("%-26s %7s %6s %6s %7s %6s %6s %5s %s" % ("track", "dur", "bpm", "swing", "centroid", "low", "onset", "score", "verdict"))
for r in rows:
    v = "EXCLUDED" if r.get("excluded") else ("PICK" if r is rows[0] else ("ok" if r["score"] > 55 else "-"))
    print("%-26s %6.0fs %6.1f %6.2f %7.0f %6.3f %6.2f %5.1f %s" % (r["file"][:26], r["dur"], r["bpm"], r["swing"], r["centroid"], r["low"], r["onset"], r["score"], v))
best = rows[0]
print("\n=> %s  (%.1f BPM, energy swing %.1f dB, duration %.0fs >= %.0fs)" % (best["file"], best["bpm"], best["swing"], best["dur"], TARGET*RULES["music"]["min_len_ratio"]))