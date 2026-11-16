# -*- coding: utf-8 -*-
"""EDL v2: Zhongshan rice-field outing -> ~3:10 cut on a 96 BPM grid."""
import json, os, sys
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs"); FR = os.path.join(WORK, "frames")
probe = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
metrics = json.load(open(os.path.join(WORK, "metrics.json"), encoding="utf-8"))
B = 0.625

def imread_u(p):
    try: return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
    except Exception: return None

# (file, beats, speed, transition, note, tag)
SHOTS = [
 ("C1763.MP4", 12, 1.0, "fade",        "开场：稻田野边的餐桌，她一袭白衣走远", "title"),
 ("C1766.MP4",  8, 1.0, "fade",        "树荫下的躺椅，午后刚刚开始", ""),
 ("C1767.MP4",  6, 1.0, "smoothleft",  "仰头看稻田的侧脸", ""),
 ("C1768.MP4",  8, 1.0, "fade",        "秋千荡起来", "fun"),
 ("C1770.MP4",  6, 1.0, "fade",        "秋千背面，稻田在轻轻晃", ""),
 ("C1771.MP4",  6, 1.0, "smoothleft",  "水杉大道，一个背影", "cap1"),
 ("C1772.MP4",  6, 1.0, "fade",        "两个人并肩走在树影里", ""),
 ("C1773.MP4",  8, 1.0, "smoothright", "树影斑驳的长路", ""),
 ("C1774.MP4",  8, 1.0, "fade",        "跟在后面慢慢走", ""),
 ("C1775.MP4",  6, 1.0, "fade",        "逆光里的白裙", ""),
 ("C1779.MP4",  6, 1.0, "smoothleft",  "树下的小市集", ""),
 ("C1780.MP4",  8, 1.0, "fade",        "穿过摊子走上大路", ""),
 ("C1782.MP4",  6, 1.0, "fadewhite",   "金黄的稻田第一次铺开", "cap2"),
 ("C1783.MP4", 10, 1.0, "fade",        "水车立在稻田尽头", ""),
 ("C1784.MP4",  6, 1.0, "fade",        "风把稻穗吹成一片浪", ""),
 ("C1785.MP4",  6, 1.0, "fade",        "水车缓缓地转", ""),
 ("C1786.MP4",  6, 1.0, "fade",        "路边一丛小黄花", ""),
 ("C1790.MP4",  6, 1.0, "fade",        "稻田里的小径", ""),
 ("C1796.MP4",  8, 1.0, "fade",        "稻田边的木栈道", ""),
 ("C1798.MP4",  8, 1.0, "smoothright", "低角度的稻浪", ""),
 ("C1801.MP4",  8, 1.0, "fade",        "栈道上走远的一群人", ""),
 ("C1802.MP4",  6, 1.0, "fade",        "田边站着的两个人", ""),
 ("C1810.MP4",  8, 1.0, "fade",        "她举起相机拍稻子", ""),
 ("C1811.MP4",  8, 1.0, "smoothleft",  "田埂上的两个人", ""),
 ("C1812.MP4",  6, 1.0, "fade",        "踩着步子过田边", ""),
 ("C1814.MP4",  6, 1.0, "fade",        "回头一笑", "hero"),
 ("C1821.MP4",  8, 1.0, "fade",        "红雕塑立在田中央", ""),
 ("C1826.MP4",  8, 1.0, "fade",        "栏杆边的合影", ""),
 ("C1828.MP4",  6, 1.0, "fade",        "稻子高过了人", ""),
 ("C1829.MP4",  8, 1.0, "fade",        "树影下的整片金黄", ""),
 ("C1830.MP4",  6, 1.0, "fade",        "风停了一下", ""),
 ("C1834.MP4",  6, 1.0, "fade",        "水车底下走过", ""),
 ("C1836.MP4",  8, 1.0, "fade",        "她逆光走过来", "hero"),
 ("C1837.MP4",  6, 1.0, "fade",        "田里的白鹅", "cute"),
 ("C1838.MP4",  6, 1.0, "fade",        "鸭子排队走过", "cute"),
 ("C1839.MP4",  8, 1.0, "fade",        "田埂上的黑猪", "cute"),
 ("C1840.MP4",  8, 1.0, "fade",        "鸡在旁边刨土", "cute"),
 ("C1841.MP4",  8, 1.0, "smoothup",    "水车木轮的特写", ""),
 ("C1842.MP4",  6, 0.6, "fade",        "慢下来，轮子还在转", ""),
 ("C1848.MP4",  8, 1.0, "fadewhite",   "太阳低下去，稻田变金", "cap3"),
 ("C1849.MP4",  6, 1.0, "fade",        "逆光的稻穗", ""),
 ("C1850.MP4",  8, 1.0, "fade",        "两个人走在金色的缝里", ""),
 ("C1851.MP4",  6, 1.0, "fade",        "背影渐渐远了", ""),
 ("C1853.MP4",  6, 1.0, "fade",        "田中小路", ""),
 ("C1854.MP4", 10, 1.0, "fade",        "举起手机，笑成一团", "joy"),
 ("C1855.MP4",  8, 1.0, "fade",        "蓝天下的水车", ""),
 ("C1856.MP4",  6, 1.0, "fade",        "水车与云", ""),
 ("C1858.MP4", 10, 1.0, "fade",        "整片稻田，远处是城", "wide"),
 ("C1859.MP4", 10, 1.0, "fade",        "最后一镜：金色一直铺到天边", "end"),
]

def frame_paths(f):
    d = os.path.join(FR, os.path.splitext(f)[0])
    return sorted(os.path.join(d, x) for x in os.listdir(d)) if os.path.isdir(d) else []

def win_rows(f, s, d_src):
    rows = metrics.get(f, [])
    return [r for r in rows if s <= (int(r["t"])-1)*0.5 < s+d_src] or rows

def levels_for(f, s, d_src):
    ps = []
    for r in win_rows(f, s, d_src):
        p = os.path.join(FR, os.path.splitext(f)[0], r["t"]+".jpg")
        im = imread_u(p)
        if im is None: continue
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        ps.append(np.percentile(g, [2, 50, 98]))
    if not ps: return dict(p2=8, p50=120, p98=248)
    arr = np.median(np.array(ps), axis=0)
    return dict(p2=float(arr[0]), p50=float(arr[1]), p98=float(arr[2]))

shots = []
for i, (f, beats, spd, xf, note, tag) in enumerate(SHOTS):
    dur = beats*B; d_src = dur*spd
    total = probe[f]["dur"]
    lo = max(0.2, total*0.05); hi = total - d_src - max(0.2, total*0.03)
    rows = metrics.get(f, [])
    def score(s):
        sel = win_rows(f, s, d_src)
        sh = np.median([r["sharp"] for r in sel]); br = np.median([r["bright"] for r in sel])
        return sh - max(0.0, 235-br)*0.35 - max(0.0, br-235)*0.6
    s0 = 0.4
    best, bs = -1e9, s0
    if hi > lo:
        for cand in np.arange(lo, hi, 0.25):
            v = score(cand)
            if v > best: best, bs = v, float(cand)
    s = round(float(np.clip(bs, 0, total-d_src-0.05)), 3)
    lv = levels_for(f, s, d_src)
    sel = win_rows(f, s, d_src)
    shots.append(dict(i=i, file=f, start=s, dur=round(dur,3), src=round(d_src,3), speed=spd,
        xf=xf, note=note, tag=tag, warm=round(i/max(1,len(SHOTS)-1),3),
        sharp=round(float(np.median([r["sharp"] for r in sel])),1),
        sat=round(float(np.median([r["sat"] for r in sel])),1),
        p2=round(lv["p2"],1), p50=round(lv["p50"],1), p98=round(lv["p98"],1),
        tc=probe[f].get("tc")))

XF_DUR = {"fade":0.625, "smoothleft":0.625, "smoothright":0.625, "smoothup":0.625, "fadewhite":0.625}
total_t = sum(s["dur"] for s in shots) - sum(XF_DUR[s["xf"]] for s in shots[1:])
# timeline position of each shot (transition starts)
pos, t = [], 0.0
for s in shots:
    pos.append(round(t,3))
    t += s["dur"] - (XF_DUR[s["xf"]] if s["i"]>0 else 0)
print("shots %d  raw %.1fs  final %.2fs = %.2f bars = %d:%05.2f" % (len(shots), sum(s["dur"] for s in shots), total_t, total_t/B/4, int(total_t//60), total_t%60))
print("min sharp %.0f  (shot %s)" % (min(s["sharp"] for s in shots), min(shots, key=lambda s: s["sharp"])["file"]))
json.dump(dict(fps=30, w=1920, h=1080, bpm=96, beat=B, xfade=XF_DUR, shots=shots, total=round(total_t,3), pos=pos),
          open(os.path.join(WORK, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for s, p in zip(shots, pos):
    print("%02d %6.2f %s @%5.2f d=%4.2f %-11s sh=%6.1f p2=%3.0f p50=%3.0f p98=%3.0f w=%.2f %s" % (
        s["i"], p, s["file"], s["start"], s["dur"], s["xf"], s["sharp"], s["p2"], s["p50"], s["p98"], s["warm"], s["note"]))
