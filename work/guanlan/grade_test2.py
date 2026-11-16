
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
V = {
 "p1": "curves=r='0/0.010 0.5/0.505 0.85/0.845 1/0.905':g='0/0.010 0.5/0.480 0.85/0.830 1/0.900':b='0/0.014 0.5/0.515 0.85/0.850 1/0.910',eq=saturation=0.95:contrast=1.04,vibrance=0.14,colorbalance=rs=-0.010:bs=0.016:rh=0.014:bh=-0.010",
 "p2": "curves=all='0/0.018 0.25/0.262 0.5/0.515 0.80/0.800 1/0.912',eq=saturation=0.93:contrast=1.06:gamma=1.01,vibrance=0.20,colorbalance=rs=-0.006:bs=0.024:rm=0.004:rh=0.020:bh=-0.014",
 "p3": "curves=all='0/0.030 0.25/0.272 0.5/0.528 0.80/0.805 1/0.940',eq=saturation=1.02:contrast=1.02,vibrance=0.06,colorbalance=rs=-0.004:bs=0.008:rh=0.010:bh=-0.004",
 "p4": "curves=all='0/0.026 0.25/0.255 0.5/0.500 0.80/0.790 1/0.900',eq=saturation=0.90:contrast=1.10:gamma=0.99,vibrance=0.22,colorbalance=rs=-0.014:bs=0.030:rh=0.026:bh=-0.018,unsharp=5:5:0.5:5:5:0",
}
outs=[]
for tag in ["D","F"]:
    for name,f in V.items():
        p=os.path.join(T,"p_%s_%s.png"%(tag,name))
        subprocess.run([FF,"-v","error","-y","-i",os.path.join(T,"src_%s.png"%tag),"-vf",f+",scale=800:-2",p],check=True)
        outs.append((tag,name,p))
ins=sum([["-i",o[2]] for o in outs],[])
fc="".join("[%d:v]"%i for i in range(8))+"xstack=inputs=8:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0"
subprocess.run([FF,"-v","error","-y"]+ins+["-filter_complex",fc,os.path.join(T,"grade2.jpg")],check=True)
print("ok")
