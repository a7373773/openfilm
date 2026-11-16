
import subprocess, os
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft4.mp4"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
# graded vs original pairs
pairs=[("E", os.path.join(SRC,"C1915S03.MP4"), 0.90, 15.20),
       ("A", os.path.join(SRC,"C1910S03.MP4"), 1.60, 3.20)]
ins=[]; 
for tag,src,tv,tg in pairs:
    o=os.path.join(T,"orig_%s.png"%tag); g=os.path.join(T,"grad_%s.png"%tag)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%tv,"-i",src,"-frames:v","1","-vf","scale=900:-2",o],check=True)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%tg,"-i",V,"-frames:v","1","-vf","scale=900:-2",g],check=True)
    ins += [o,g]
fc="".join("[%d:v]"%i for i in range(4))+"xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0"
subprocess.run([FF,"-v","error","-y"]+sum([["-i",p] for p in ins],[])+["-filter_complex",fc,os.path.join(T,"ab.jpg")],check=True)
print("ok")
