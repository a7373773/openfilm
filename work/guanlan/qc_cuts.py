
import subprocess, numpy as np
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft4.mp4"
w,h=192,108
p=subprocess.run([FF,"-v","error","-i",V,"-vf","fps=30,scale=%d:%d"%(w,h),"-f","rawvideo","-pix_fmt","gray","-"],capture_output=True)
d=np.frombuffer(p.stdout,np.uint8)
n=len(d)//(w*h); fr=d[:n*w*h].reshape(n,h,w).astype(np.float32)
diff=np.abs(np.diff(fr,axis=0)).mean(axis=(1,2))
# contrast change
mean=np.array([f.mean() for f in fr])
cuts=[]
for i in range(1,len(diff)):
    if diff[i] > max(6.0, np.percentile(diff,99.3)*0.5) or abs(mean[i]-mean[i-1])>25:
        cuts.append((i+1)/30.0)
# merge close
merged=[]
for c in cuts:
    if not merged or c-merged[-1]>0.25: merged.append(c)
print("frames",n,"dur %.2f"%(n/30))
print("cuts:", [round(c,2) for c in merged])
beat=60.0/77.0
res=[]
for c in merged:
    k=round((c-1.538)/beat)  # grid offset: first blend start
    for off in (0.0,1.538):
        kk=round((c-off)/beat); dd=abs(c-off-kk*beat)
        res.append(dd)
print("beat=%.4fs  min dist to grid: %s"%(beat, [round(min(abs(c-o-round((c-o)/beat)*beat) for o in (0,1.538,0.4)),3) for c in merged]))
