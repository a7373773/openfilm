
import subprocess, os
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft4.mp4"
subprocess.run([FF,"-v","error","-y","-ss","24.6","-t","2.2","-i",V,"-vf","fps=5,scale=480:-2,tile=4x3","-frames:v","1",os.path.join(T,"endt.jpg")],check=True)
subprocess.run([FF,"-v","error","-y","-ss","27.2","-i",V,"-frames:v","1",os.path.join(T,"endcard_frame.png")],check=True)
subprocess.run([FF,"-v","error","-y","-ss","15.2","-i",V,"-frames:v","1",os.path.join(T,"peak_frame.png")],check=True)
print("ok")
