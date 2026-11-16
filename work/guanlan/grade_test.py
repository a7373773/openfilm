
import os, subprocess
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
T = r"C:\Users\30308\AppData\Local\Temp\glwork"
frames = [("C1910S03.MP4", 1.5, "A"), ("C1913S03.MP4", 1.2, "D"), ("C1916S03.MP4", 1.8, "F")]
SRCIN = {}
for f,t,tag in frames:
    out=os.path.join(T,"src_%s.png"%tag)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%t,"-i",os.path.join(SRC,f),"-frames:v","1",out],check=True)
    SRCIN[tag]=out

V = {
 "orig": None,
 "v1_print": "curves=all='0/0.012 0.25/0.262 0.5/0.520 0.78/0.800 1/0.930',eq=contrast=1.03:saturation=1.02,colorbalance=rs=-0.008:bs=0.014:rh=0.014:bh=-0.010,vibrance=0.05",
 "v2_warm": "curves=all='0/0.020 0.25/0.268 0.5/0.530 0.78/0.795 1/0.915',eq=contrast=1.05:saturation=1.00:gamma=1.02,colorbalance=rs=-0.015:bs=0.006:rh=0.030:gh=0.006:bh=-0.020,vibrance=0.03",
 "v3_soft": "curves=all='0/0.030 0.25/0.280 0.5/0.535 0.78/0.790 1/0.900',eq=contrast=0.98:saturation=0.97,colorbalance=rs=-0.004:bs=0.020:rh=0.020:bh=-0.006,vibrance=0.08",
}
outs={}
for tag in ["A","D","F"]:
    for name,f in V.items():
        if f is None:
            outs[(tag,name)]=SRCIN[tag]; continue
        p=os.path.join(T,"g_%s_%s.png"%(tag,name))
        subprocess.run([FF,"-v","error","-y","-i",SRCIN[tag],"-vf",f+",scale=640:-2",p],check=True)
        outs[(tag,name)]=p
# tile 3 rows x 4 cols
rows=[]
for tag in ["A","D","F"]:
    rows.append([outs[(tag,n)] for n in V])
names=list(V)
subprocess.run([FF,"-v","error","-y"]+sum([[ "-i",p] for r in rows for p in r],[])+
  ["-filter_complex","""
""".join([]) or "".join("[%d:v]scale=640:-2[s%d];"%(i,i) for i in range(12))+
   "".join("[s%d]"%(i) for i in range(12))+"xstack=inputs=12:layout=0_0|w0_0|w0+w1_0|w0+w1+w2_0|0_h0|w0_h0|w0+w1_h0|w0+w1+w2_h0|0_h0+h4|w0_h0+h4|w0+w1_h0+h4|w0+w1+w2_h0+h4[out]",
   "-map","[out]",os.path.join(T,"grade_test.jpg")],check=True)
print("ok", os.path.join(T,"grade_test.jpg"))
