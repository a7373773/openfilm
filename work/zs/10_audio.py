# -*- coding: utf-8 -*-
import json, os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
WORK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\zs"
MUS = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\music\src\Carefree.mp3"
EDL = json.load(open(os.path.join(WORK,"edl.json"),encoding="utf-8")); T = EDL["total"]
out = os.path.join(WORK,"bgm.wav")
af = "afade=t=in:st=0:d=2.0,afade=t=out:st=%.2f:d=4.0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" % (T-4.0)
cmd = [FF,"-hide_banner","-nostdin","-y","-loglevel","error","-stream_loop","-1","-i",MUS,
       "-t","%.3f"%T,"-af",af,"-ac","2","-ar","48000",out]
p = subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if p.returncode: print(p.stderr.decode("utf-8","replace")[-1500:]); sys.exit(1)
print("bgm ok", out, os.path.getsize(out))
