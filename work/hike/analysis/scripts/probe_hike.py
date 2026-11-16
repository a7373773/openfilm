# -*- coding: utf-8 -*-
import subprocess, re, os, json
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"

def probe(path):
    p = subprocess.run([FF, "-hide_banner", "-i", path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = p.stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", txt)
    dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else None
    v = {}; has_audio = False
    for line in txt.splitlines():
        if "Stream #" in line and "Video:" in line:
            mr = re.search(r"(\d{3,4})x(\d{3,4})", line)
            mf = re.search(r"([\d.]+) fps", line)
            v = {"w": int(mr.group(1)) if mr else None, "h": int(mr.group(2)) if mr else None,
                 "fps": float(mf.group(1)) if mf else None}
        if "Stream #" in line and "Audio:" in line:
            has_audio = True
    return dur, v, has_audio

files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
out = {}
tot = 0.0
print("%-16s %7s %5s %5s %7s %5s" % ("file","dur","w","h","fps","audio"))
for f in files:
    d, v, a = probe(os.path.join(SRC, f))
    out[f] = {"duration": d, "w": v.get("w"), "h": v.get("h"), "fps": v.get("fps"), "audio": a}
    tot += d or 0
    print("%-16s %7.2f %5s %5s %7.2f %5s" % (f, d or 0, v.get("w"), v.get("h"), v.get("fps") or 0, a))
print("TOTAL %.2f s, files %d" % (tot, len(files)))
json.dump(out, open(os.path.join(OUT, "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
