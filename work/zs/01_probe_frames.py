# -*- coding: utf-8 -*-
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
SRC  = os.path.join(ROOT, "素材", "中山")
WORK = os.path.join(ROOT, "work", "zs")
FR   = os.path.join(WORK, "frames")
os.makedirs(FR, exist_ok=True)

files = sorted([f for f in os.listdir(SRC) if f.upper().endswith(".MP4")])

def probe(f):
    p = subprocess.run([FF, "-hide_banner", "-i", os.path.join(SRC, f)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s = p.stderr.decode("utf-8", "replace")
    d = {"file": f}
    m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", s)
    if m: d["dur"] = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
    m = re.search(r"creation_time\s+:\s+(\S+)", s)
    if m: d["ctime"] = m.group(1)
    m = re.search(r"timecode\s+:\s+(\d+):(\d+):(\d+):(\d+)", s)
    if m:
        d["tc"] = "%s:%s:%s:%s" % m.groups()
        d["tc_sec"] = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) + int(m.group(4))/50.0
    m = re.search(r"Video: h264.*?, (\d+)x(\d+).*?, ([\d.]+) fps", s)
    if m: d["w"] = int(m.group(1)); d["h"] = int(m.group(2)); d["fps"] = float(m.group(3))
    m = re.search(r"bitrate:\s+(\d+) kb/s", s)
    if m: d["kbps"] = int(m.group(1))
    return d

def frames(d):
    f = d["file"]; base = os.path.splitext(f)[0]
    out = os.path.join(FR, base)
    os.makedirs(out, exist_ok=True)
    if len(os.listdir(out)) >= 4: return len(os.listdir(out))
    subprocess.run([FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
        "-i", os.path.join(SRC, f), "-vf", "fps=2,scale=480:-2",
        "-q:v", "3", os.path.join(out, "%03d.jpg")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return len(os.listdir(out))

with ThreadPoolExecutor(max_workers=6) as ex:
    metas = list(ex.map(probe, files))
print("probed", len(metas))

with ThreadPoolExecutor(max_workers=4) as ex:
    counts = list(ex.map(frames, metas))
for d, c in zip(metas, counts): d["nframes"] = c
print("frames done", sum(counts))

json.dump(metas, open(os.path.join(WORK, "probe.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# quick stats
metas.sort(key=lambda d: d.get("tc_sec", 0))
tot = sum(d.get("dur", 0) for d in metas)
print("total_dur_s", round(tot, 1), "clips", len(metas))
print("first", metas[0]["file"], metas[0].get("tc"), metas[0].get("ctime"))
print("last ", metas[-1]["file"], metas[-1].get("tc"), metas[-1].get("ctime"))
durs = sorted(d.get("dur", 0) for d in metas)
print("dur min/med/max", durs[0], durs[len(durs)//2], durs[-1])
