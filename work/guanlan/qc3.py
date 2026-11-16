
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft3.mp4"
subprocess.run([FF,"-v","error","-y","-ss","0.9","-t","2.4","-i",V,"-vf","fps=5,scale=420:-2,tile=4x3","-frames:v","1",os.path.join(T,"open_seq.jpg")],check=True)
subprocess.run([FF,"-v","error","-y","-ss","20.9","-t","4.9","-i",V,"-vf","fps=3.5,scale=420:-2,tile=4x4","-frames:v","1",os.path.join(T,"end_seq.jpg")],check=True)
print("ok")
