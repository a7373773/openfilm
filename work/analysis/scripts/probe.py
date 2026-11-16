# -*- coding: utf-8 -*-
import subprocess, re, os, json, sys

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"

def probe(path):
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = p.stderr
    dur = None; vinfo = ""
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", txt)
    if m:
        dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    for line in txt.splitlines():
        if "Stream #" in line and "Video:" in line:
            vinfo = line.strip()
            break
    return dur, vinfo

if __name__ == "__main__":
    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
    out = {}
    tot = 0.0
    for f in files:
        d, v = probe(os.path.join(SRC, f))
        out[f] = {"duration": d, "vinfo": v}
        tot += d or 0
        print(f"{f}\t{d}\t{v[:110]}", flush=True)
    print("TOTAL_SEC", round(tot,2), "files", len(files))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "probe.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
