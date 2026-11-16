
import subprocess, os
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
D = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\观澜版画村"
W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\render\draft4.mp4"
files=[("draft",W),("master",os.path.join(D,"一版秋花_画质版_1080p.mp4")),("share",os.path.join(D,"一版秋花_分享版_1080p.mp4"))]
ins=[]
for tag,p in files:
    o=os.path.join(T,"cmp_%s.png"%tag)
    subprocess.run([FF,"-v","error","-y","-ss","9.6","-i",p,"-frames:v","1","-vf","crop=960:540:480:300",o],check=True)
    ins.append(o)
fc="".join("[%d:v]"%i for i in range(3))+"hstack=inputs=3"
subprocess.run([FF,"-v","error","-y"]+sum([["-i",p] for p in ins],[])+["-filter_complex",fc,os.path.join(T,"cmp.jpg")],check=True)
for tag,p in files:
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    import re
    print(tag, os.path.basename(p), [l.strip() for l in r.splitlines() if "Duration" in l or "Video:" in l or "Audio:" in l])
