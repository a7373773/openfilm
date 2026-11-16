
import os, subprocess, numpy as np, cv2, json
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
FILES = ["C1910S03.MP4","C1911S03.MP4","C1912S03.MP4","C1913S03.MP4","C1914S03.MP4","C1915S03.MP4","C1916S03.MP4"]
casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,"haarcascade_frontalface_default.xml"))
body = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,"haarcascade_upperbody.xml"))
out={}
for f in FILES:
    p=os.path.join(SRC,f)
    cap_frames=subprocess.run([FF,"-v","error","-i",p,"-vf","fps=2,scale=960:-2","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True,cwd="C:/Users/30308/AppData/Local/Temp").stdout
    # infer size
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    import re
    m=re.search(r"(\d{3,5})x(\d{3,5})",r); W,H=int(m.group(1)),int(m.group(2)); w=960; h=int(960*H/W/2)*2
    n=len(cap_frames)//(w*h*3)
    faces=0; bodies=0
    for i in range(n):
        img=np.frombuffer(cap_frames[i*w*h*3:(i+1)*w*h*3],np.uint8).reshape(h,w,3)
        g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        if len(casc.detectMultiScale(g,1.15,5,minSize=(40,40)))>0: faces+=1
        if len(body.detectMultiScale(g,1.1,3,minSize=(60,60)))>0: bodies+=1
    out[f]=dict(frames=n,faces=faces,upperbody=bodies)
print(json.dumps(out,indent=1))
