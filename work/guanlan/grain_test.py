
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
BASE = ("curves=r='0/0.010 0.5/0.505 0.85/0.845 1/0.905':g='0/0.010 0.5/0.480 0.85/0.830 1/0.900':b='0/0.014 0.5/0.515 0.85/0.850 1/0.910',"
        "eq=saturation=0.95:contrast=1.04,vibrance=0.14,"
        "colorbalance=rs=-0.010:bs=0.016:rh=0.014:bh=-0.010,unsharp=5:5:0.45:5:5:0")
V = {
 "g3": "noise=alls=3:allf=t,vignette=angle=PI/6",
 "g6": "noise=alls=6:allf=t,vignette=angle=PI/6",
 "g6v": "noise=alls=6:allf=t,vignette=angle=PI/4.5",
 "none": "null",
}
outs=[]
for i,(k,v) in enumerate(V.items()):
    p=os.path.join(T,"gr_%s.png"%k)
    subprocess.run([FF,"-v","error","-y","-i",os.path.join(T,"src_D.png"),"-vf",
                    (BASE+","+v) if k!="none" else BASE+",noise=alls=0,vignette=angle=PI/2",
                    p],check=True)
    # crop 960x540 center
    c=os.path.join(T,"gc_%s.png"%k)
    subprocess.run([FF,"-v","error","-y","-i",p,"-vf","crop=960:540:480:270",c],check=True)
    outs.append(c)
ins=sum([["-i",o] for o in outs],[])
fc="".join("[%d:v]"%i for i in range(4))+"xstack=inputs=4:layout=0_0|w0_0|0_h0|w0_h0"
subprocess.run([FF,"-v","error","-y"]+ins+["-filter_complex",fc,os.path.join(T,"grain_test.jpg")],check=True)
print("ok")
