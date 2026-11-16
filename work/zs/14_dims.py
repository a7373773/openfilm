# -*- coding: utf-8 -*-
import os, re, subprocess, sys, json, collections
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\中山"
rows = []
for f in sorted(os.listdir(SRC)):
    if not f.upper().endswith(".MP4"): continue
    s = subprocess.run([FF,"-hide_banner","-i",os.path.join(SRC,f)],stdout=subprocess.PIPE,stderr=subprocess.PIPE).stderr.decode("utf-8","replace")
    m = re.search(r"Video: (\w+).*?(\d{3,4})x(\d{3,4})", s)
    sar = re.search(r"\[SAR (\d+):(\d+) DAR (\d+):(\d+)\]", s)
    rot = re.search(r"rotation of ([\-\d.]+) degrees", s) or re.search(r"rotate\s*:\s*([\-\d.]+)", s)
    rows.append((f, m.group(1) if m else "?", m.group(2) if m else "?", m.group(3) if m else "?",
                 sar.group(1)+":"+sar.group(2) if sar else "-", sar.group(3)+":"+sar.group(4) if sar else "-",
                 rot.group(1) if rot else "0"))
c = collections.Counter([(r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows])
print("distinct formats:")
for k, v in c.items(): print("  ", k, "x", v)
odd = [r for r in rows if (r[2], r[3]) != ("1920", "1080") or r[4] != "1:1" or r[6] not in ("0", "0.0")]
print("odd files:", len(odd))
for r in odd[:15]: print("  ", r)
json.dump(rows, open(r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\zs\dims.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
