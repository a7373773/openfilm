
from PIL import Image, ImageDraw
W,H=1920,1080
OUT=r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\graphics"
im=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(im)
# glow
for r,a in ((16,40),(12,80),(8,235)):
    d.ellipse([960-r,1050-r,960+r,1050+r], fill=(255,122,61,a))
im.save(OUT+r"\11_bar_dot.png")
print("dot ok")
