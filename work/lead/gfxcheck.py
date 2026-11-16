
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
TMP = os.path.join(W, "render", "chk"); os.makedirs(TMP, exist_ok=True)
# 1) alpha coverage of each graphics asset
G = os.path.join(W, "graphics")
for f in sorted(os.listdir(G)):
    im = Image.open(os.path.join(G, f)).convert("RGBA")
    a = np.asarray(im)[..., 3]
    print("%-18s alpha>10: %5.2f%%  bbox=%s" % (f, 100*(a>10).mean(), im.getbbox()))
# 2) frames from test render: title present vs absent
for t, name in [(2.0, "title"), (5.5, "lt"), (12.0, "end"), (8.0, "plain")]:
    p = os.path.join(TMP, "f_%s.png" % name)
    subprocess.run([FF, "-v", "error", "-y", "-ss", "%.2f" % t, "-i", os.path.join(W, "render", "test1.mp4"),
                    "-frames:v", "1", p], check=True)
    a = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
    Y = 0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    white = (Y > 240).mean()*100
    # region checks
    title_reg = Y[380:660, 140:1000].mean()
    lt_reg = Y[880:1000, 120:900].mean()
    bar = Y[1040:1056, 120:1800].mean()
    print("%-6s t=%4.1f  white%%=%.2f  title_reg=%.1f lt_reg=%.1f bar=%.1f" % (name, t, white, title_reg, lt_reg, bar))
