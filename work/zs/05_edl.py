# -*- coding: utf-8 -*-
"""Build the edit decision list for the Zhongshan rice-field outing."""
import json, os, sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs"); FR = os.path.join(WORK, "frames")
probe = {d["file"]: d for d in json.load(open(os.path.join(WORK, "probe.json"), encoding="utf-8"))}
metrics = json.load(open(os.path.join(WORK, "metrics.json"), encoding="utf-8"))

B = 0.625  # one beat @96bpm
# file, src start guess, beats(2beats=1.25s ..), speed, transition, zoom, note
SHOTS = [
 # ---- 0 片头 ----
 ("C1763.MP4", 1.2, 11, 1.0, "fade",      1.00, "开场：稻田野餐桌，她一袭白衣走远", "title"),
 # ---- 1 午后·抵达（12:05-12:34） ----
 ("C1766.MP4", 0.4,  8, 1.0, "fade",      1.03, "树荫下躺椅，午后刚刚开始", ""),
 ("C1767.MP4", 0.3,  6, 1.0, "smoothleft",1.02, "仰头看稻田的侧脸", ""),
 ("C1768.MP4", 0.6,  8, 1.0, "fade",      1.02, "秋千荡起来", "fun"),
 ("C1770.MP4", 1.2,  6, 1.0, "fade",      1.03, "秋千背面，稻田在晃", ""),
 ("C1771.MP4", 0.2,  6, 1.0, "smoothleft",1.02, "水杉大道，背影", "cap1"),
 ("C1772.MP4", 0.2,  6, 1.0, "fade",      1.02, "两人并肩走在树影里", ""),
 ("C1773.MP4", 1.0,  8, 1.0, "smoothright",1.04,"树影斑驳的长路", ""),
 ("C1774.MP4", 0.4,  8, 1.0, "fade",      1.03, "跟在后面走", ""),
 ("C1775.MP4", 0.3,  6, 1.0, "fade",      1.02, "逆光里的白裙", ""),
 ("C1779.MP4", 0.2,  6, 1.0, "smoothleft",1.02, "树下小市集", ""),
 ("C1780.MP4", 0.5,  8, 1.0, "fade",      1.03, "穿过摊子走上大路", ""),
 # ---- 2 稻田·水车（15:32-15:53） ----
 ("C1782.MP4", 0.2,  6, 1.0, "fadewhite", 1.02, "金黄的稻田第一次铺开", "cap2"),
 ("C1783.MP4", 0.4, 10, 1.0, "fade",      1.05, "水车在稻田尽头", ""),
 ("C1784.MP4", 0.4,  6, 1.0, "fade",      1.02, "风把稻穗吹成一片浪", ""),
 ("C1785.MP4", 0.3,  6, 1.0, "fade",      1.03, "水车缓缓转", ""),
 ("C1786.MP4", 0.4,  6, 1.0, "fade",      1.04, "路边一丛小黄花", "cap3"),
 ("C1796.MP4", 0.6,  8, 1.0, "fade",      1.03, "稻田边的木栈道", ""),
 ("C1798.MP4", 1.0,  8, 1.0, "smoothright",1.03,"低角度的稻浪", ""),
 ("C1810.MP4", 0.2,  8, 1.0, "fade",      1.03, "她举起相机拍稻子", ""),
 ("C1811.MP4", 0.4,  8, 1.0, "smoothleft",1.03, "田埂上两个人", ""),
 ("C1812.MP4", 0.6,  6, 1.0, "fade",      1.02, "踩着步子过田边", ""),
 ("C1814.MP4", 0.4,  6, 1.0, "fade",      1.05, "回头一笑", "hero"),
 # ---- 3 村巷·小动物（15:53-16:20） ----
 ("C1821.MP4", 1.0,  8, 1.0, "fade",      1.03, "红雕塑立在田中央", "cap4"),
 ("C1826.MP4", 0.3,  8, 1.0, "fade",      1.03, "栏杆边合影", ""),
 ("C1836.MP4", 0.4,  8, 1.0, "fade",      1.03, "逆光走过来", "hero"),
 ("C1837.MP4", 0.2,  6, 1.0, "fade",      1.04, "田里的白鹅", "cute"),
 ("C1838.MP4", 0.6,  6, 1.0, "fade",      1.03, "鸭子排队走过", "cute"),
 ("C1839.MP4", 0.4,  8, 1.0, "fade",      1.03, "田埂上的黑猪", "cute"),
 ("C1840.MP4", 1.0,  8, 1.0, "fade",      1.03, "鸡在旁边刨土", "cute"),
 ("C1841.MP4", 0.4,  8, 1.0, "smoothup",  1.03, "水车木轮特写", ""),
 ("C1842.MP4", 0.6,  6, 0.6, "fade",      1.03, "慢下来，轮子转", ""),
 # ---- 4 黄金时刻（16:20-16:42） ----
 ("C1848.MP4", 0.4,  8, 1.0, "fadewhite", 1.03, "太阳低下来，稻田变金", "cap5"),
 ("C1849.MP4", 0.3,  6, 1.0, "fade",      1.03, "逆光的稻穗", ""),
 ("C1850.MP4", 0.4,  8, 1.0, "fade",      1.03, "两个人走在金色的缝里", ""),
 ("C1851.MP4", 0.4,  6, 1.0, "fade",      1.02, "背影远了", ""),
 ("C1853.MP4", 0.3,  6, 1.0, "fade",      1.03, "田中小路", ""),
 ("C1854.MP4", 0.5, 10, 1.0, "fade",      1.04, "举起手机，笑成一团", "joy"),
 ("C1855.MP4", 0.3,  8, 1.0, "fade",      1.03, "蓝天下的水车", ""),
 ("C1856.MP4", 0.4,  6, 1.0, "fade",      1.03, "水车与云", ""),
 ("C1858.MP4", 1.0, 10, 1.0, "fade",      1.04, "整片稻田，远处是城", "wide"),
 ("C1859.MP4", 0.8, 10, 1.0, "fade",      1.05, "最后一镜，金色一直铺到天边", "end"),
]

def win_stats(f, s, d_src):
    rows = metrics.get(f, [])
    n = len(rows)
    sel = [r for r in rows if s <= (int(r["t"])-1)*0.5 < s+d_src]
    if not sel: sel = rows
    return (float(np.median([r["sharp"] for r in sel])),
            float(np.median([r["bright"] for r in sel])),
            float(np.median([r["sat"] for r in sel])))

shots, t = [], 0.0
for i, (f, s0, beats, spd, xf, zoom, note, tag) in enumerate(SHOTS):
    dur = beats * B
    d_src = dur * spd
    total = probe[f]["dur"]
    # best window search: maximise median sharpness, stay away from first/last 6%
    lo = max(0.15, total*0.06); hi = total - d_src - max(0.15, total*0.04)
    best, bs = -1e9, s0
    if hi > lo:
        for cand in np.arange(lo, hi, 0.25):
            sh, br, sa = win_stats(f, cand, d_src)
            score = sh - max(0.0, 235-br)*0.35 - max(0.0, br-235)*0.6
            if score > best: best, bs = score, float(cand)
    s = round(bs, 3)
    sh, br, sa = win_stats(f, s, d_src)
    shots.append(dict(i=i, file=f, start=s, dur=round(dur,3), src=round(d_src,3), speed=spd,
                      xf=xf, zoom=zoom, note=note, tag=tag,
                      sharp=round(sh,1), bright=round(br,1), sat=round(sa,1), tc=probe[f].get("tc"),
                      warm=round(i/max(1,len(SHOTS)-1), 3)))
    t += dur

XF = {x[4]: 0.625 for x in SHOTS}
overlap = sum(XF[s["xf"]] for s in shots[1:])
final = t - overlap
print("shots", len(shots), "sum_dur %.2f" % t, "final %.2f s (%.2f bars)" % (final, final/B/4))
print("min sharp", min(s["sharp"] for s in shots), "max", max(s["sharp"] for s in shots))
json.dump(dict(fps=30, w=1920, h=1080, bpm=96, beat=B, shots=shots, total=round(final,3)),
          open(os.path.join(WORK, "edl.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for s in shots:
    print("%02d %s @%5.2f d=%4.2f %-11s sh=%5.1f br=%5.1f w=%.2f %s" % (s["i"], s["file"], s["start"], s["dur"], s["xf"], s["sharp"], s["bright"], s["warm"], s["note"]))
