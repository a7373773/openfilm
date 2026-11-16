
import sys, os, json
sys.path.insert(0, r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead")
import beat_analysis as ba, numpy as np
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\music\src"
for f in ["Cattails.mp3","Sapphire Isle.mp3","Wallpaper.mp3","Open Those Bright Eyes.mp3","Life of Riley.mp3"]:
    p=os.path.join(SRC,f)
    x,sr=ba.decode(p); dur=len(x)/sr
    flux,fr=ba.onset_env(x,sr); tops,_,_=ba.estimate_bpm(flux,fr)
    bpm=tops[0][1]
    # brightness: spectral centroid mean
    spec=np.abs(np.fft.rfft(x[:sr*60])) if len(x)>sr*60 else np.abs(np.fft.rfft(x))
    freqs=np.fft.rfftfreq(len(x[:sr*60]) if len(x)>sr*60 else len(x), 1/sr)
    cen=float((spec*freqs).sum()/(spec.sum()+1e-9))
    # rms
    hop=sr//10; rms=np.sqrt(np.convolve(x*x,np.ones(hop)/hop,mode='same'))[::hop]
    per=[round(float(rms[i:i+10].mean()),3) for i in range(0,min(len(rms),sr*10//10), sr//10)]
    print("%-28s dur=%6.2f bpm=%6.2f cand=%s centroid=%6.0fHz"%(
        f, dur, bpm, [round(b) for b,v in tops[:3]], cen))
    print("   rms/1s:", per[:40])
