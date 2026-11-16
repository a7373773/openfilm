
import numpy as np
from PIL import Image
p=r'D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\预览_分镜缩略图.jpg'
im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(np.float32)
print("sheet", im.size)
W,H=480,270; PAD=8; LH=34; COLS=3
for k in range(18):
    r_,c_=divmod(k,COLS)
    x=PAD+c_*(W+PAD); y=PAD+r_*(H+LH+PAD)
    t=a[y:y+H, x:x+W]
    print("tile %02d luma=%.1f std=%.1f"%(k+1,t.mean(),t.std()))
