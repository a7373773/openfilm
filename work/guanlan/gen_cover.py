
import os, subprocess
from PIL import Image, ImageDraw, ImageFont
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\观澜版画村"
V = os.path.join(OUT, "一版秋花_画质版_1080p.mp4")
SERIF = r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"
F = lambda s: ImageFont.truetype(SERIF, s)
subprocess.run([FF,"-v","error","-y","-ss","15.50","-i",V,"-frames:v","1",os.path.join(T,"cv.png")],check=True)
base = Image.open(os.path.join(T,"cv.png")).convert("RGB")
W,H = base.size
grad = Image.new("L",(1,H),0)
for y in range(H):
    u = max(0.0,(y-H*0.30)/(H*0.70))
    grad.putpixel((0,y), int((u**1.5)*205))
dark = Image.new("RGB",(W,H),(6,8,7))
img = Image.composite(dark, base, grad.resize((W,H)))
# 左侧再压一点，让文字有底
lg = Image.new("L",(W,1),0)
for x in range(W):
    u = max(0.0,(1-x/(W*0.55)))
    lg.putpixel((x,0), int((u**1.6)*70))
img = Image.composite(Image.new("RGB",(W,H),(6,8,7)), img, lg.resize((W,H)))
d = ImageDraw.Draw(img)
x,y = 116, 792
d.text((x,y),"一版秋花", font=F(112), fill=(250,247,240))
d.line([x+6,y+168,x+6+168,y+168], fill=(238,234,226), width=2)
d.text((x+8,y+190),"观澜 · 版画村     2026.11", font=F(31), fill=(228,224,216))
img.save(os.path.join(OUT,"封面_1080p.jpg"), quality=92)
try: os.remove(os.path.join(OUT,"_coverA.jpg"))
except: pass
print("cover ok", img.size)
