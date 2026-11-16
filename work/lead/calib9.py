
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib9"
os.makedirs(TMP, exist_ok=True)
f,t="REC-0005-A.mp4",41.5
LV="colorlevels=rimin=0.05:rimax=0.97:gimin=0.05:gimax=0.97:bimin=0.05:bimax=0.97"
CURVE="curves=all='0/0.010 0.25/0.255 0.5/0.525 0.80/0.800 1/0.920'"
tests={
 "u1_10_lv_curve":"format=yuv444p10le,"+LV+","+CURVE,
 "u2_10_lv_curve_down":"format=yuv444p10le,"+LV+","+CURVE+",format=yuv420p",
 "u3_10_lv_curve_eq":"format=yuv444p10le,"+LV+","+CURVE+",format=yuv420p,eq=saturation=1.03",
 "u4_8_lv_curve_eq":LV+","+CURVE+",eq=saturation=1.03",
 "u5_8_lv_curve_eq_vib":LV+","+CURVE+",eq=saturation=1.03,vibrance=0.12",
 "u6_8_curve_eq_vib":CURVE+",eq=saturation=1.03,vibrance=0.12",
 "u7_10_lv_curve_vib_only":"format=yuv444p10le,"+LV+","+CURVE+",format=yuv420p,vibrance=0.12",
}
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    mx=a.max(axis=2);mn=a.min(axis=2);s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    return "p50=%.3f p95=%.3f sat=%.3f Y=%.3f cliphi=%.4f"%(np.percentile(Y,50),np.percentile(Y,95),s.mean(),Y.mean(),(Y>0.99).mean())
for k,v in tests.items():
    out=os.path.join(TMP,k+".png")
    vf="scale=1920:1080:flags=lanczos,"+v
    p=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],capture_output=True)
    print("%-28s %s"%(k, "ERR" if p.returncode!=0 else stats(out)))
