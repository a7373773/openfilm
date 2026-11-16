# -*- coding: utf-8 -*-
"""Analyze BGM: decode -> onset envelope -> BPM + downbeat phase + energy curve."""
import subprocess, sys, os, json, math
import numpy as np

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"

def decode(path, sr=22050):
    cmd = [FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    a = np.frombuffer(p.stdout, dtype=np.float32)
    return a, sr

def onset_env(x, sr, hop=256, win=1024):
    n = 1 + max(0, (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    idx = np.clip(idx, 0, len(x) - 1)
    frames = x[idx] * np.hanning(win)[None, :]
    # log-mel-ish: use magnitude spectrum bands
    spec = np.abs(np.fft.rfft(frames, axis=1))
    bands = np.array_split(np.arange(spec.shape[1]), 24)
    mel = np.array([spec[:, b].mean(axis=1) for b in bands]).T
    mel = np.log1p(mel * 10.0)
    flux = np.maximum(0, np.diff(mel, axis=0)).sum(axis=1)
    flux = np.concatenate([[0], flux])
    fr = sr / hop
    return flux, fr

def estimate_bpm(flux, fr, lo=60, hi=180):
    f = flux - flux.mean()
    ac = np.correlate(f, f, mode="full")[len(f) - 1:]
    ac /= (ac[0] + 1e-12)
    lags = np.arange(len(ac)) / fr
    cand = {}
    for bpm in np.arange(lo, hi + 0.1, 0.25):
        lag = 60.0 / bpm
        i = lag * fr
        i0 = int(math.floor(i))
        if i0 + 1 < len(ac):
            v = ac[i0] * (1 - (i - i0)) + ac[i0 + 1] * (i - i0)
            cand[bpm] = v
    good = sorted(((v, b) for b, v in cand.items()), reverse=True)
    return good[:6], ac, lags

def beat_phase(flux, fr, bpm):
    """Find phase offset (sec) of strongest periodic pulse."""
    period = 60.0 / bpm
    best = None
    for ph in np.arange(0, period, 0.01):
        idx = np.arange(ph * fr, len(flux), period * fr).astype(int)
        idx = idx[idx < len(flux)]
        s = float(flux[idx].mean()) if len(idx) else 0.0
        if best is None or s > best[1]:
            best = (ph, s)
    return best[0]

def main(path):
    x, sr = decode(path)
    dur = len(x) / sr
    flux, fr = onset_env(x, sr)
    tops, ac, lags = estimate_bpm(flux, fr)
    print("file  :", path)
    print("dur   : %.2f s  sr=%d" % (dur, sr))
    print("top bpm candidates (score, bpm):")
    for v, b in tops:
        print("   %.3f  %.2f  (period %.3fs)" % (v, b, 60.0 / b))
    bpm = tops[0][1]
    ph = beat_phase(flux, fr, bpm)
    print("chosen bpm %.2f  beat period %.4f s  phase %.3f s" % (bpm, 60.0 / bpm, ph))
    # energy per second (RMS) for structural mapping
    hop = sr // 10
    rms = np.sqrt(np.convolve(x * x, np.ones(hop) / hop, mode="same"))[::hop]
    secs = np.arange(len(rms)) / ((sr / hop))
    print("rms per second:")
    print("  " + " ".join("%.3f" % v for v in rms[::10][:60]))
    out = {"file": path, "dur": dur, "bpm": bpm, "beat": 60.0 / bpm, "phase": float(ph),
           "candidates": [[float(b), float(v)] for v, b in tops]}
    return out

if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1])))
