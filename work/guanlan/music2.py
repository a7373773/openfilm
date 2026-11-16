
import sys, os, numpy as np, json
sys.path.insert(0, r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\lead")
import beat_analysis as ba
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\music\src"
for name in ["Cattails.mp3","Sapphire Isle.mp3"]:
    p=os.path.join(SRC,name)
    x,sr=ba.decode(p); dur=len(x)/sr
    flux,fr=ba.onset_env(x,sr)
    tops,_,_=ba.estimate_bpm(flux,fr)
    print("==",name,"dur %.2f"%dur)
    print("  bpm cands:", [(round(b,2), round(v,3)) for b,v in tops])
    bpm=tops[0][1]; ph=ba.beat_phase(flux,fr,bpm)
    print("  bpm %.2f beat %.4f phase %.3f"%(bpm,60/bpm,ph))
    hop=sr//10
    rms=np.sqrt(np.convolve(x*x,np.ones(hop)/hop,mode='same'))[::hop]
    rms10 = rms[::10]  # per second
    print("  rms 0-70s:", " ".join("%.2f"%v for v in rms10[:70]))
