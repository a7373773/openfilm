# -*- coding: utf-8 -*-
import json, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8")
WORK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\zs"
EDL = json.load(open(os.path.join(WORK,"edl.json"),encoding="utf-8"))
T = EDL["total"]; pos = EDL["pos"]; shots = EDL["shots"]
def ts(t):
    t = max(0.0, t); return "%d:%02d:%05.2f" % (int(t//3600), int((t%3600)//60), t%60)

HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Microsoft YaHei,102,&H00FFFFFF,&H000000FF,&H12121212,&H96000000,-1,0,0,0,100,100,12,0,1,4,6,5,60,60,60,1
Style: Sub,Microsoft YaHei,42,&H00FFFFFF,&H000000FF,&H12121212,&H96000000,0,0,0,0,100,100,8,0,1,3,4,5,60,60,60,1
Style: Cap,Microsoft YaHei,52,&H00FFFFFF,&H000000FF,&H12121212,&H96000000,-1,0,0,0,100,100,10,0,1,3,4,7,120,60,96,1
Style: End,Microsoft YaHei,66,&H00FFFFFF,&H000000FF,&H12121212,&H96000000,-1,0,0,0,100,100,10,0,1,4,5,5,60,60,60,1
Style: Credit,Microsoft YaHei,30,&H00F0F0F0,&H000000FF,&H12121212,&H96000000,0,0,0,0,100,100,2,0,1,2,3,2,60,60,44,1
Style: Glow,Microsoft YaHei,10,&H00000000,&H00000000,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
def emit(style, t0, t1, pos_tpl, an, fade, text, layer=1, glow=None):
    if glow:
        blur, alpha, fs_add, bold = glow
        ev.append("Dialogue: 0,%s,%s,%s,,0,0,0,,{\\an%d%s\\fad(%d,%d)\\blur%d\\1c&H000000&\\1a&H%02X&\\bord0\\shad0\\fs%d\\fsp0}%s" % (
            ts(t0), ts(t1), style, an, pos_tpl, fade, fade, blur, alpha, fs_add, text))
    ev.append("Dialogue: %d,%s,%s,%s,,0,0,0,,{\\an%d%s\\fad(%d,%d)}%s" % (layer, ts(t0), ts(t1), style, an, pos_tpl, fade, fade, text))

# opening title (soft dark glow behind white type)
emit("Title", 1.1, 6.2, "\\pos(960,452)", 5, 900, "中山 · 稻田采风", 1, (30, 0x4A, 112, -1))
emit("Sub",   2.0, 6.2, "\\pos(960,568)", 5, 900, "2026.11.14 晴 · 户外采风", 1, (24, 0x56, 46, 0))

# section captions
for tag, text in [("cap1","午后 · 抵达"),("cap2","稻田 · 采风"),("cap3","日落之前")]:
    idx = [s["i"] for s in shots if s["tag"] == tag][0]
    t0 = pos[idx] + 0.45
    emit("Cap", t0, t0+3.4, "\\pos(120,884)", 7, 600, text, 1, (26, 0x50, 56, -1))

# end card
t_end = T - 8.0
emit("End", t_end, T-1.6, "\\pos(960,512)", 5, 1100, "中山　2026.11.14", 1, (30, 0x50, 72, -1))
emit("Credit", t_end+0.6, T-1.6, "\\pos(960,1022)", 2, 1100,
     "音乐：Sapphire Isle — Kevin MacLeod (incompetech.com) · CC BY 4.0", 1, (24, 0x58, 32, 0))

out = os.path.join(WORK,"titles.ass")
open(out,"w",encoding="utf-8-sig").write(HDR + "\n".join(ev) + "\n")
shutil.copyfile(out, r"C:\Users\30308\AppData\Local\Temp\zs_titles.ass")
print("subs ok", len(ev))