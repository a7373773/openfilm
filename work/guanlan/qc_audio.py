
import subprocess, numpy as np, os
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft4.mp4"
p=subprocess.run([FF,"-v","error","-i",V,"-f","f32le","-ac","1","-ar","8000","-"],capture_output=True)
a=np.frombuffer(p.stdout,dtype=np.float32)
sr=8000
print("audio dur %.2fs peak %.3f"%(len(a)/sr, float(np.abs(a).max())))
sec=[float(np.sqrt((a[i*sr:(i+1)*sr]**2).mean())) for i in range(int(len(a)/sr))]
print("rms/s:", " ".join("%.2f"%v for v in sec))
