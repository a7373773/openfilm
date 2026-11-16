
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft2.mp4"
for tag,ss,dur,fps,tile in [("s1",14.6,3.2,4,"4x4"),("s2",20.6,4.8,3,"4x4")]:
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%ss,"-t","%.2f"%dur,"-i",V,
                    "-vf","fps=%d,scale=400:-2,tile=%s"%(fps,tile),"-frames:v","1",
                    os.path.join(T,tag+".jpg")],check=True)
r=subprocess.run([FF,"-hide_banner","-i",V,"-af","volumedetect","-f","null","-"],capture_output=True)
print(r.stderr.decode("utf-8","replace")[-400:])
