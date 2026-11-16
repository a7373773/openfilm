
import subprocess, os
import numpy as np
from PIL import Image
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
TMP = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead\calib7"
os.makedirs(TMP, exist_ok=True)
f,t="REC-0005-A.mp4",41.5
LV="colorlevels=rimin=0.06:rimax=0.95:gimin=0.06:gimax=0.95:bimin=0.06:bimax=0.95"
CURVE="curves=all='0/0.010 0.25/0.255 0.5/0.525 0.80/0.800 1/0.920'"
tests={
 "t0_none":"",
 "t1_lv":LV,
 "t2_10_lv":"format=yuv444p10le,"+LV,
 "t3_10_lv_curve":"format=yuv444p10le,"+LV+","+CURVE,
 "t4_10_lv_curve_eq":"format=yuv444p10le,"+LV+","+CURVE+",eq=saturation=1.05:contrast=1.03",
 "t5_full":"format=yuv444p10le,"+LV+","+CURVE+",eq=saturation=1.05:contrast=1.03,vibrance=0.18,colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012,format=yuv420p",
 "t6_curve_only":CURVE,
 "t7_lv_curve_8bit":LV+","+CURVE,
}
def stats(p):
    a=np.asarray(Image.open(p).convert("RGB")).astype(np.float32)/255.0
    Y=0.299*a[...,0]+0.587*a[...,1]+0.114*a[...,2]
    mx=a.max(axis=2);mn=a.min(axis=2);s=np.where(mx>0,(mx-mn)/(mx+1e-6),0)
    return "p50=%.3f p95=%.3f sat=%.3f Ymean=%.3f"%(np.percentile(Y,50),np.percentile(Y,95),s.mean(),Y.mean())
for k,v in tests.items():
    out=os.path.join(TMP,k+".png")
    vf="scale=1920:1080:flags=lanczos"+(((","+v) if v else ""))
    p=subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1","-vf",vf,"-pix_fmt","rgb24",out],capture_output=True)
    if p.returncode!=0: print("%-20s ERR %s"%(k,p.stderr.decode("utf-8","replace")[-300:])); continue
    print("%-20s %s"%(k,stats(out)))
