
import os, subprocess, numpy as np, cv2, json, re
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
TMP = r"C:\Users\30308\AppData\Local\Temp\glwork"
FILES = ["C1910S03.MP4","C1913S03.MP4","C1915S03.MP4"]
casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades,"haarcascade_frontalface_default.xml"))
tiles=[]
for f in FILES:
    p=os.path.join(SRC,f)
    r=subprocess.run([FF,"-hide_banner","-i",p],capture_output=True).stderr.decode("utf-8","replace")
    m=re.search(r"(\d{3,5})x(\d{3,5})",r); W,H=int(m.group(1)),int(m.group(2)); w=960; h=int(960*H/W/2)*2
    raw=subprocess.run([FF,"-v","error","-i",p,"-vf","fps=2,scale=960:-2","-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True).stdout
    n=len(raw)//(w*h*3)
    for i in range(n):
        img=np.frombuffer(raw[i*w*h*3:(i+1)*w*h*3],np.uint8).reshape(h,w,3).copy()
        g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        fs=casc.detectMultiScale(g,1.15,5,minSize=(40,40))
        for (x,y,ww,hh) in fs:
            cv2.rectangle(img,(x,y),(x+ww,y+hh),(0,0,255),3)
        if len(fs):
            cv2.putText(img,"%s %.1fs"%(f[:5],i/2),(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,255,255),2)
            tiles.append(img)
print("tiles",len(tiles))
cols=2
th=tiles[0].shape[0]; tw=tiles[0].shape[1]
rows=(len(tiles)+cols-1)//cols
sheet=np.zeros((rows*th,cols*tw,3),np.uint8)
for i,t in enumerate(tiles):
    r,c=divmod(i,cols); sheet[r*th:r*th+th,c*tw:c*tw+tw]=t
p=os.path.join(TMP,"faces.jpg"); cv2.imwrite(p,sheet); print(p, sheet.shape)
