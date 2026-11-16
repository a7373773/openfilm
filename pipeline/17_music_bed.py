# -*- coding: utf-8 -*-
"""17_music_bed: cut the chosen track to the film length with soft fades.
usage: python 17_music_bed.py <track> <total_s> <out.wav> [from_end 0|1]"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FF

track, total, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
from_end = len(sys.argv) > 4 and sys.argv[4] == "1"
dur = float(subprocess.run([FF, "-hide_banner", "-i", track], stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE).stderr.decode("utf-8", "replace").split("Duration: ")[1].split(",")[0]
            .replace(":", "") if False else 0) if False else None
s = subprocess.run([FF, "-hide_banner", "-i", track], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stderr.decode("utf-8", "replace")
import re
m = re.search(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)", s)
dur = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
start = max(0.0, dur - total - 0.15) if from_end else 0.0
af = "afade=t=in:st=0:d=1.5,afade=t=out:st=%.2f:d=3.0,loudnorm=I=-17:TP=-1.5:LRA=8,aresample=48000" % (total - 3.0)
cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error", "-ss", "%.2f" % start, "-t", "%.2f" % total,
       "-i", track, "-af", af, "-ac", "2", "-ar", "48000", out]
p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if p.returncode: print(p.stderr.decode("utf-8", "replace")[-1200:]); sys.exit(1)
print("bed ok start=%.2f len=%.2f -> %s" % (start, total, out))