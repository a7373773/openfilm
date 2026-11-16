# -*- coding: utf-8 -*-
"""EDL v4: no repeated subject, landscape-safe. 96 BPM grid."""
import json, os, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs"); FR = os.path.join(WORK, "frames")
probe = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
metrics = json.load(open(os.path.join(WORK, "metrics.json"), encoding="utf-8"))
B = 0.625

# (file, beats, speed, transition, note, tag, subject-group)
SHOTS = [
 ("C1763.MP4", 18, 1.00, "fade",        "开场：稻田边的白桌，她一袭白衣走远", "title", "opening"),
 ("C1766.MP4",  8, 1.00, "fade",        "伞下躺椅，午后刚刚开始", "", "chair"),
 ("C1768.MP4",  8, 1.00, "fade",        "秋千荡起来", "fun", "swing"),
 ("C1773.MP4", 10, 1.00, "smoothright", "水杉大道，树影斑驳的长路", "cap1", "avenue"),
 ("C1775.MP4",  7, 1.00, "smoothleft",  "两个人并肩走，逆光里的白裙", "", "avenue"),
 ("C1780.MP4",  8, 1.00, "fade",        "穿过单车摊，走上大路", "", "market"),
 ("C1783.MP4", 14, 0.80, "fadewhite",   "水车立在稻田尽头（慢镜）", "cap2", "wheel-wide"),
 ("C1786.MP4",  6, 1.00, "fade",        "路边一丛小黄花", "", "flower"),
 ("C1790.MP4",  7, 1.00, "fade",        "稻田里的小径通向远处", "", "path"),
 ("C1798.MP4", 12, 1.00, "smoothright", "低角度，稻穗贴着镜头", "", "rice-close"),
 ("C1801.MP4",  9, 1.00, "fade",        "栈道上走远的一群人", "", "boardwalk"),
 ("C1803.MP4",  8, 1.00, "fade",        "沿着田边水渠往前走", "", "path"),
 ("C1809.MP4",  9, 1.00, "fade",        "她举起相机拍稻子", "", "shoot"),
 ("C1814.MP4",  7, 1.00, "fade",        "回头一笑", "hero", "portrait"),
 ("C1821.MP4",  8, 1.00, "circleopen",  "红雕塑立在田中央", "cap3", "sculpture"),
 ("C1826.MP4",  7, 1.00, "fade",        "栏杆边的合影", "", "portrait"),
 ("C1829.MP4", 12, 1.00, "fade",        "稻子高过了人", "", "rice-wide"),
 ("C1834.MP4",  7, 1.00, "fade",        "从水车底下走过", "", "wheel-under"),
 ("C1836.MP4",  9, 1.00, "fade",        "她逆光走过来", "hero", "portrait"),
 ("C1837.MP4",  7, 1.00, "circleopen",  "田里的白鹅", "cute", "goose"),
 ("C1839.MP4",  7, 1.00, "fade",        "田埂上的黑猪", "cute", "pig"),
 ("C1841.MP4",  8, 1.00, "smoothup",    "水车木轮的特写", "", "wheel-close"),
 ("C1846.MP4",  6, 1.00, "fade",        "村口的水渠，房子倒影", "", "canal"),
 ("C1851.MP4",  7, 1.00, "dissolve",    "村口的小店，天开始发暖", "cap4", "shop"),
 ("C1850.MP4",  9, 1.00, "fade",        "两个人穿过高高的稻子", "", "golden-people"),
 ("C1854.MP4", 12, 1.00, "fade",        "举起手机，笑成一团", "joy", "golden-people"),
 ("C1855.MP4",  7, 1.00, "fade",        "蓝天下的水车", "", "wheel-blue"),
 ("C1859.MP4", 16, 1.00, "fade",        "最后一镜：金色一直铺到天边", "end", "finale"),
]
ROTATED = {"C1769.MP4", "C1779.MP4"}

def imread_u(p):
    try: return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception: return None

def win_rows(f, s, d):
    rows = metrics.get(f, [])
    return [r for r in rows if s <= (int(r["t"])-1)*0.5 < s+d] or rows

def levels_for(f, s, d):
    ps = []
    for r in win_rows(f, s, d):
        im = imread_u(os.path.join(FR, os.path.splitext(f)[0], r["t"]+".jpg"))
        if im is None: continue
        ps.append(np.percentile(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), [2, 50, 98]))
    a = np.median(np.array(ps), axis=0) if ps else np.array([8, 120, 248])
    return float(a[0]), float(a[1]), float(a[2])

XF_DUR = {"fade":0.625,"smoothleft":0.625,"smoothright":0.625,"smoothup":0.625,
          "fadewhite":0.625,"dissolve":0.625,"circleopen":0.625}
shots = []
for i, (f, beats, spd, xf, note, tag, grp) in enumerate(SHOTS):
    assert f not in ROTATED, f + " is a portrait/rotated take"
    total = probe[f]["dur"]; dmax = total - 0.30
    dur = beats*B; speed = spd
    if dur*speed > dmax:
        if dmax/dur >= 0.78: speed = round(dmax/dur, 3)
        else:
            while dur > 2.5+B and dmax/dur < 0.78: dur -= B
            speed = round(min(1.0, dmax/dur), 3)
    d_src = round(dur*speed, 3)
    lo, hi = max(0.15, total*0.04), total - d_src - 0.10
    def score(s):
        sel = win_rows(f, s, d_src)
        return np.median([r["sharp"] for r in sel]) - max(0.0, 235-np.median([r["bright"] for r in sel]))*0.35
    bs, best = None, -1e9
    if hi > lo:
        for cand in np.arange(lo, hi, 0.2):
            v = score(cand)
            if v > best: best, bs = v, float(cand)
    if bs is None: bs = max(0.0, hi)
    s = round(float(np.clip(bs, 0.0, max(0.0, total-d_src-0.05))), 3)
    p2, p50, p98 = levels_for(f, s, d_src)
    sel = win_rows(f, s, d_src)
    shots.append(dict(i=i, file=f, start=s, dur=round(dur,3), src=d_src, speed=speed, xf=xf,
        xfd=XF_DUR[xf], note=note, tag=tag, grp=grp, warm=round(i/max(1,len(SHOTS)-1),3),
        sharp=round(float(np.median([r["sharp"] for r in sel])),1),
        p2=round(p2,1), p50=round(p50,1), p98=round(p98,1), tc=probe[f].get("tc")))

files = [s["file"] for s in shots]
assert len(files) == len(set(files)), "duplicate file in EDL"
total_t = sum(s["dur"] for s in shots) - sum(s["xfd"] for s in shots[1:])
pos, t = [], 0.0
for s in shots:
    pos.append(round(t,4)); t += s["dur"] - s["xfd"]
json.dump(dict(fps=30,w=1920,h=1080,bpm=96,beat=B,xfade=XF_DUR,shots=shots,total=round(total_t,3),pos=pos),
          open(os.path.join(WORK,"edl.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("shots %d  final %.2fs = %d:%05.2f  unique files %d" % (len(shots), total_t, int(total_t//60), total_t%60, len(set(files))))
import collections
g = collections.Counter(s["grp"] for s in shots)
print("groups:", dict(g))
for s,p in zip(shots,pos):
    print("%02d %6.2f %s @%5.2f d=%4.2f %-11s sh=%6.1f p50=%3.0f | %s" % (s["i"],p,s["file"],s["start"],s["dur"],s["xf"],s["sharp"],s["p50"],s["note"]))