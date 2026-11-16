# -*- coding: utf-8 -*-
"""Deliverable docs + preview contact sheet (deduped cut)."""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
WORK = os.path.join(ROOT, "work", "zs")
OUT = os.path.join(ROOT, "成片", "中山采风"); os.makedirs(OUT, exist_ok=True)
EDL = json.load(open(os.path.join(WORK,"edl.json"), encoding="utf-8"))
shots = EDL["shots"]; T = EDL["total"]
pos, t = [], 0.0
for s in shots:
    pos.append(round(t,3)); t += s["dur"] - s["xfd"]
def mmss(x): return "%d:%05.2f" % (int(x//60), x % 60)
def tag_pos(tag):
    for s, p in zip(shots, pos):
        if s["tag"] == tag: return p
    return T

sel = list(range(0, len(shots), 2))
F = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 17)
TW, TH, COLS = 426, 240, 3
rows = (len(sel)+COLS-1)//COLS
sheet = Image.new("RGB", (TW*COLS, (TH+24)*rows), (14,14,14)); dr = ImageDraw.Draw(sheet)
for k, i in enumerate(sel):
    p = os.path.join(WORK,"clips","shot_%02d.mp4" % i); jpg = os.path.join(WORK,"pv_%02d.jpg" % i)
    subprocess.run([FF,"-v","error","-y","-ss","%.2f"%(shots[i]["dur"]*0.55),"-i",p,"-frames:v","1","-q:v","3",jpg])
    if os.path.exists(jpg):
        sheet.paste(Image.open(jpg).convert("RGB").resize((TW,TH)), ((k%COLS)*TW, (k//COLS)*(TH+24)))
    dr.text(((k%COLS)*TW+5, (k//COLS)*(TH+24)+TH+3), "#%02d %s  %s" % (i, mmss(pos[i]), shots[i]["note"][:22]), fill=(235,235,235), font=F)
pv = os.path.join(OUT, "预览_分镜缩略图.jpg"); sheet.save(pv, quality=88)

L = ["# 镜头表 · 中山稻田采风", "",
     "成片总长 **%s** ｜ 1920x1080 横屏 / 30fps / H.264 High ｜ %d 个镜头 / %d 个素材文件（无重复镜头）｜ 96 BPM 节拍网格" % (
         mmss(T), len(shots), len(set(s["file"] for s in shots))), "",
     "| # | 成片时间 | 源文件 | 源入点 | 时长 | 速度 | 转场 | 画面 |", "|---|---|---|---|---|---|---|---|"]
XF = {"fade":"交叉淡化","smoothleft":"左滑","smoothright":"右滑","smoothup":"上滑",
      "fadewhite":"白场淡入","dissolve":"溶解","circleopen":"圆形展开"}
for s, p in zip(shots, pos):
    sp = "原速" if abs(s["speed"]-1)<1e-3 else ("%.2fx 慢镜" % s["speed"] if s["speed"]<1 else "%.2fx" % s["speed"])
    L.append("| %d | %s–%s | %s | %s | %.2fs | %s | %s | %s |" % (
        s["i"]+1, mmss(p), mmss(p+s["dur"]), s["file"], mmss(s["start"]), s["dur"], sp, XF.get(s["xf"], s["xf"]), s["note"]))
open(os.path.join(OUT,"镜头表.md"),"w",encoding="utf-8").write("\n".join(L)+"\n")

mp4 = os.path.join(OUT, "中山采风_稻田_1080p.mp4")
share = os.path.join(OUT, "中山采风_稻田_分享版.mp4")
sz = lambda p: "%.1f MB" % (os.path.getsize(p)/1e6) if os.path.exists(p) else "-"
s1, s2, s3 = tag_pos("cap2"), tag_pos("cap3"), tag_pos("cap4")
notes = """# 中山 · 稻田采风 ｜ 交付说明

## 一、成片

| 文件 | 规格 | 用途 |
|---|---|---|
| ~BT~中山采风_稻田_1080p.mp4~BT~ | 1920×1080 横屏 / 30fps / H.264 High / AAC 48kHz 立体声 / %s | 高清母版，可留存或再进剪映精修 |
| ~BT~中山采风_稻田_分享版.mp4~BT~ | 同上，码率更低 / %s | 发微信、小红书、B站 |
| ~BT~预览_分镜缩略图.jpg~BT~ | 每 2 个镜头取 1 帧，带时间码 | 快速核对画面 |

**总长 %s**，%d 个镜头，取自 99 个素材文件（8.9 分钟原始素材）。**每个场景只用一个镜头**，不重复。

## 二、两处修正

1. **去掉重复镜头**：原来 48 个镜头里，水杉大道、稻田、水车、动物这些同机位的镜头反复出现。现在按“一个场景/机位只用一次”重排，
   同一类内容（比如水车）最多留两个**景别明显不同**的（一个远景、一个特写），其余换成别的段落，或者直接删掉。29 个镜头，每个都只出现一次。
2. **去掉竖屏和变形**：素材里有 2 条（C1769、C1779）带 90° 旋转标记——是竖着拍的，之前被拉伸成横屏，所以人看着是变形的。现在这两条全部剔除；
   渲染链也改成“等比放大后居中裁切”，以后即使混进竖屏素材也只会裁，不会再拉伸。全片统一 1920×1080 横屏。

## 三、结构：按真实时间线走四段

| 段落 | 时间 | 内容 |
|---|---|---|
| 午后 · 抵达 | 0:00–%s | 田边白桌与躺椅、秋千、水杉大道、单车摊 |
| 稻田 · 水车 | %s–%s | 水车立在稻田尽头、小黄花、稻浪、栈道、田埂上举相机的人 |
| 村巷 · 小动物 | %s–%s | 红雕塑、栏杆合影、稻子高过人头、白鹅、黑猪、水车木轮 |
| 日落之前 | %s–%s | 村口小店、两人穿过金色稻子、举手机笑成一团、最后一镜 |

素材是 11 月 14 日 12:05–16:42 一整天拍的。16:20 之后光线真正暖起来，出了最好看的金色，所以高潮和结尾都留给了这一段。

**节奏**：全片按 96 BPM 排，每个镜头时长都是 0.625 秒（一拍）的整数倍，切点落在拍子上，卡点明显但不机械。
29 个镜头里只有 9 个用方向性转场（左滑/右滑/上滑/白场/溶解/圆形展开），其余都是 0.6 秒交叉淡化——动效跟着镜头运动走，不抢画面。

## 四、镜头是怎么挑的

1. **逐秒像素分析**：99 个文件按 0.5 秒抽帧（共 1078 帧），算锐度（拉普拉斯方差）、边缘密度、亮度、饱和度，排掉虚焦和过曝段落。
2. **窗口寻优**：每个镜头在素材里自动找“锐度最高、亮度最正”的窗口作为入点，不是简单取开头。
3. **去重**：同一场景的镜头按“锐度高 + 景别信息量大”保留一条，其余删掉。
4. **肉眼复核**：拉分镜墙确认机位、人物走向、构图；白鹅、黑猪、水车木轮这几个是看过图手动留下的。

## 五、调色（免费、可复现）

目标是**轻快、温馨、通透**，不压成电影感的深色：

~FENCE~
逐镜头曝光对齐   colorlevels 按每镜头 p2/p98 轻微归一（强度 0.55 / 0.30），只动亮度不动色相
整体亮度微调     eq brightness ±0.035（按 p50 向 0.42 靠）
高光滚降         curves: 0/0.012  0.25/0.262  0.5/0.53  0.78/0.788  1/0.945   ← 正午白天空不再刺眼
饱和度/对比      eq saturation=1.05  contrast=1.03
自然饱和度       vibrance 0.13
冷暖分割         colorbalance：阴影偏一点青、高光偏暖，暖度随片长从 0 推到 1
                 高光 R +0.020 到 +0.046 / B −0.014 到 −0.032；阴影 R −0.006 到 −0.010 / B +0.010 到 +0.014
锐化             unsharp 5:5:0.30
~FENCE~

暖度不是固定的，而是随片子推进从 0 走到 1——前半段中性的午后感，后半段金色逐渐浓起来，跟素材真实的日落进程对上。

## 六、音乐

**Carefree — Kevin MacLeod**（incompetech.com），**CC BY 4.0**。96 BPM，尤克里里 + 吉他 + 马林巴 + 钟琴 + 轻打击乐。

⚠️ **CC BY 4.0 要求署名**，发布时请在简介注明：

> 音乐：Carefree — Kevin MacLeod (incompetech.com)，依据 CC BY 4.0 授权使用 https://creativecommons.org/licenses/by/4.0/

片尾字幕里也带了这行署名。

## 七、想改的话

| 你的想法 | 我怎么改 |
|---|---|
| 想更长 | 加回被删掉的同类镜头（会重新出现重复感），或者把镜头拉长 |
| 某个镜头不好看 | 报镜头号（看 ~BT~镜头表.md~BT~）或截个图，换同段落其它素材 |
| 更暖 / 更冷 | 暖度曲线整体加减 |
| 竖屏 9:16 | 需要重新构图，约 10 分钟 |
| 换音乐 | 库里还有 Cattails（民谣暖）、Life of Riley（更跳脱）、Sapphire Isle（纯钢琴） |

## 八、中间产物

~BT~work/zs/~BT~：~BT~probe.json~BT~、~BT~metrics.json~BT~（1078 帧指标）、~BT~edl.json~BT~（剪辑决策表）、
~BT~08_render.py~BT~（渲染脚本）、~BT~titles.ass~BT~（字幕）、~BT~bgm.wav~BT~（配乐）。
""" % (sz(mp4), sz(share), mmss(T), len(shots), mmss(s1), mmss(s1), mmss(s2), mmss(s2), mmss(s3), mmss(s3), mmss(T))
notes = notes.replace("~BT~", chr(96)).replace("~FENCE~", chr(96)*3)
open(os.path.join(OUT,"说明.md"),"w",encoding="utf-8").write(notes)
print("docs ok")
