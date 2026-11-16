
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft2.mp4"
subprocess.run([FF,"-v","error","-y","-i",V,"-vf","fps=0.85,scale=340:-2,tile=6x5","-frames:v","1",os.path.join(T,"strip.jpg")],check=True)
for t,name in [(1.2,"f_title"),(8.0,"f_a"),(15.6,"f_e"),(20.0,"f_slow"),(27.0,"f_end")]:
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",V,"-frames:v","1",os.path.join(T,name+".jpg")],check=True)
# audio check
r=subprocess.run([FF,"-v","error","-i",V,"-af","volumedetect","-f","null","-"],capture_output=True)
print(r.stderr.decode("utf-8","replace")[-500:])
