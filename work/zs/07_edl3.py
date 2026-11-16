# -*- coding: utf-8 -*-
"""EDL v3: auto-fit each shot to the clip length, beat-aligned to 96 BPM."""
import json, os, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs"); FR = os.path.join(WORK, "frames")
probe = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
metrics = json.load(open(os.path.join(WORK, "metrics.json"), encoding="utf-8"))
B = 0.625

SHOTS = [
 ("C1763.MP4", 12, 1.0, "fade",        "开场：稻田边的白桌，她一袭白衣走远", "title"),
 ("C1766.MP4",  8, 1.0, "fade",        "树荫下的躺椅，午后刚开始", ""),
 ("C1767.MP4",  6, 1.0, "smoothleft",  "仰头看稻田的侧脸", ""),
 ("C1768.MP4",  8, 1.0, "fade",        "秋千荡起来", "fun"),
 ("C1770.MP4",  6, 1.0, "fade",        "秋千背面，稻田在晃", ""),
 ("C1771.MP4",  5, 1.0, "smoothleft",  "水杉大道，一个背影", "cap1"),
 ("C1772.MP4",  4, 1.0, "fade",        "两个人并肩走在树影里", ""),
 ("C1773.MP4",  8, 1.0, "smoothright", "树影斑驳的长路", ""),
 ("C1774.MP4",  8, 1.0, "fade",        "跟在后面慢慢走", ""),
 ("C1775.MP4",  6, 1.0, "fade",        "逆光里的白裙", ""),
 ("C1779.MP4",  6, 1.0, "dissolve",    "树下的小市集", ""),
 ("C1780.MP4",  8, 1.0, "fade",        "穿过摊子走上大路", ""),
 ("C1782.MP4",  4, 1.0, "fadewhite",   "金黄的稻田第一次铺开", "cap2"),
 ("C1783.MP4", 10, 0.75, "fade",       "水车立在稻田尽头（慢镜）", ""),
 ("C1784.MP4",  6, 1.0, "fade",        "风把稻穗吹成一片浪", ""),
 ("C1785.MP4",  6, 1.0, "fade",        "水车缓缓地转", ""),
 ("C1786.MP4",  6, 1.0, "fade",        "路边一丛小黄花", ""),
 ("C1790.MP4",  6, 1.0, "fade",        "稻田里的小径", ""),
 ("C1796.MP4",  8, 1.0, "dissolve",    "稻田边的木栈道", ""),
 ("C1798.MP4",  8, 1.0, "smoothright", "低角度的稻浪", ""),
 ("C1801.MP4",  8, 1.0, "fade",        "栈道上走远的一群人", ""),
 ("C1802.MP4",  6, 1.0, "fade",        "田边站着的两个人", ""),
 ("C1809.MP4",  8, 1.0, "fade",        "她站在田埂上举起相机", ""),
 ("C1811.MP4",  8, 1.0, "smoothleft",  "田埂上的两个人", ""),
 ("C1812.MP4",  6, 1.0, "fade",        "踩着步子过田边", ""),
 ("C1814.MP4",  5, 1.0, "fade",        "回头一笑", "hero"),
 ("C1821.MP4",  8, 1.0, "circleopen",  "红雕塑立在田中央", ""),
 ("C1826.MP4",  5, 1.0, "fade",        "栏杆边的合影", ""),
 ("C1828.MP4",  6, 1.0, "fade",        "稻子高过了人", ""),
 ("C1829.MP4",  8, 1.0, "fade",        "树影下的整片金黄", ""),
 ("C1830.MP4",  6, 1.0, "fade",        "风停了一下", ""),
 ("C1834.MP4",  6, 1.0, "fade",        "水车底下走过", ""),
 ("C1836.MP4",  6, 1.0, "fade",        "她逆光走过来", "hero"),
 ("C1837.MP4",  5, 1.0, "circleopen",  "田里的白鹅", "cute"),
 ("C1838.MP4",  6, 1.0, "fade",        "鸭子排队走过", "cute"),
 ("C1839.MP4",  5, 1.0, "fade",        "田埂上的黑猪", "cute"),
 ("C1840.MP4",  8, 1.0, "fade",        "鸡在旁边刨土", "cute"),
 ("C1841.MP4",  8, 1.0, "smoothup",    "水车木轮的特写", ""),
 ("C1842.MP4",  6, 0.6, "fade",        "慢下来，轮子还在转", ""),
 ("C1849.MP4",  6, 1.0, "fadewhite",   "太阳低下去，稻田变金", "cap3"),
 ("C1850.MP4",  8, 1.0, "fade",        "两个人穿过高高的稻子", ""),
 ("C1851.MP4",  6, 1.0, "dissolve",    "村口的小店，天开始发暖", ""),
 ("C1853.MP4",  6, 1.0, "fade",        "田中小路上走着", ""),
 ("C1854.MP4", 10, 1.0, "fade",        "举起手机，笑成一团", "joy"),
 ("C1855.MP4",  6, 1.0, "fade",        "蓝天下的水车", ""),
 ("C1856.MP4",  6, 1.0, "fade",        "水车与云", ""),
 ("C1858.MP4", 10, 1.0, "fade",        "整片稻田，远处是城", "wide"),
 ("C1859.MP4", 10, 1.0, "fade",        "最后一镜：金色一直铺到天边", "end"),
]

def imread_u(p):
    try: return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception: return None

def win_rows(f, s, d_src):
    rows = metrics.get(f, [])
    return [r for r in rows if s <= (int(r["t"])-1)*0.5 < s+d_src] or rows

def levels_for(f, s, d_src):
    ps = []
    for r in win_rows(f, s, d_src):
        im = imread_u(os.path.join(FR, os.path.splitext(f)[0], r["t"]+".jpg"))
        if im is None: continue
        ps.append(np.percentile(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), [2, 50, 98]))
    arr = np.median(np.array(ps), axis=0) if ps else np.array([8, 120, 248])
    return float(arr[0]), float(arr[1]), float(arr[2])

XF_DUR = {"fade":0.625,"smoothleft":0.625,"smoothright":0.625,"smoothup":0.625,
          "fadewhite":0.625,"dissolve":0.625,"circleopen":0.625}
shots = []
for i, (f, beats, spd, xf, note, tag) in enumerate(SHOTS):
    total = probe[f]["dur"]; dmax = total - 0.30
    dur = beats*B; speed = spd
    if dur*speed > dmax:
        if dmax/dur >= 0.78:
            speed = round(dmax/dur, 3)
        else:
            while dur > 2.5+B and dmax/dur < 0.78:
                dur -= B
            speed = round(min(1.0, dmax/dur), 3)
    d_src = round(dur*speed, 3)
    lo, hi = max(0.15, total*0.04), total - d_src - 0.10
    def score(s):
        sel = win_rows(f, s, d_src)
        return (np.median([r["sharp"] for r in sel]) - max(0.0, 235-np.median([r["bright"] for r in sel]))*0.35)
    bs, best = None, -1e9
    if hi > lo:
        for cand in np.arange(lo, hi, 0.2):
            v = score(cand)
            if v > best: best, bs = v, float(cand)
    if bs is None: bs = max(0.0, hi)
    s = round(float(np.clip(bs, 0.0, max(0.0, total-d_src-0.05))), 3)
    p2, p50, p98 = levels_for(f, s, d_src)
    sel = win_rows(f, s, d_src)
    shots.append(dict(i=i, file=f, start=s, dur=round(dur,3), src=d_src, speed=speed,
        xf=xf, xfd=XF_DUR[xf], note=note, tag=tag, warm=round(i/max(1,len(SHOTS)-1),3),
        sharp=round(float(np.median([r["sharp"] for r in sel])),1),
        p2=round(p2,1), p50=round(p50,1), p98=round(p98,1), tc=probe[f].get("tc")))

total_t = sum(s["dur"] for s in shots) - sum(s["xfd"] for s in shots[1:])
pos, t = [], 0.0
for s in shots:
    pos.append(round(t,3)); t += s["dur"] - s["xfd"]
bad = [s["file"] for s in shots if s["start"] < 0 or s["start"]+s["src"] > probe[s["file"]]["dur"]+1e-6]
print("shots %d  final %.2fs = %d:%05.2f (%.1f bars)  bad=%s" % (len(shots), total_t, int(total_t//60), total_t%60, total_t/B/4, bad))
json.dump(dict(fps=30,w=1920,h=1080,bpm=96,beat=B,xfade=XF_DUR,shots=shots,total=round(total_t,3),pos=pos),
          open(os.path.join(WORK,"edl.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
for s,p in zip(shots,pos):
    print("%02d %6.2f %s @%5.2f d=%4.2f sp=%.2f %-10s sh=%6.1f p50=%3.0f w=%.2f | %s" % (
        s["i"],p,s["file"],s["start"],s["dur"],s["speed"],s["xf"],s["sharp"],s["p50"],s["warm"],s["note"]))
