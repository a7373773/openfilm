# -*- coding: utf-8 -*-
import json, os
WK = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\成片\爬山"
os.makedirs(OUT, exist_ok=True)
edl = json.load(open(os.path.join(WK, "edl.json"), encoding="utf-8-sig"))
shots = edl["shots"]; ov = edl.get("overlays", [])
SECN = {0: "起步", 1: "林间", 2: "爬升", 3: "开阔", 4: "登顶"}
def fmt(x):
    return "%d:%04.1f" % (int(x // 60), x - 60 * int(x // 60))
t = 0.0; rows = []
for s in shots:
    rows.append((fmt(t), s)); t += float(s["dur"]) - float(s.get("trans", 0.0) or 0.0)
TOTAL = t
L = []
L.append("# 镜头表 · 爬山《山野之间》\n")
L.append("成片总长 **%.1f 秒**（%s）｜1920x1080 / 30fps / H.264 / AAC 48kHz｜%d 个镜头｜按拍摄顺序剪辑\n" % (
    TOTAL, fmt(TOTAL), len(shots)))
L.append("| # | 成片时间 | 源文件 | 源时间码 | 时长 | 章节 | 画质档 | 转场 |")
L.append("|---|---|---|---|---|---|---|---|")
for i, (tc, s) in enumerate(rows):
    tr = s.get("trans", 0) or 0
    trs = ("%.2fs %s" % (tr, s.get("trans_type", ""))) if tr > 0.01 else "硬切"
    L.append("| %d | %s | %s | %s–%s | %.2fs | %s | %s | %s |" % (
        i + 1, tc, s["file"], fmt(float(s["start"])), fmt(float(s["start"]) + float(s["dur"])),
        float(s["dur"]), SECN.get(int(s["sec"]), "-"), s.get("grade", "-"), trs))
L.append("\n## 字幕 / 贴纸时间点\n")
L.append("| 时间 | 素材 | 说明 |")
L.append("|---|---|---|")
DESC = {"01_title.png": "标题卡《山野之间》", "08_endcard.png": "结尾卡",
        "09_bar_bg.png": "底部进度条(轨道)", "11_bar_dot.png": "进度条光点(随片移动)"}
NAMES = {"lt_01.png": "字幕：出发 / 把城市的噪音留在身后", "lt_02.png": "字幕：身体先醒过来 / 心率加快，呼吸变深",
         "lt_03.png": "字幕：林间穿行 / 找到自己的节奏", "lt_04.png": "字幕：最陡的一段 / 慢一点也没关系",
         "lt_05.png": "字幕：补给时刻 / 水·盐分·一点耐心", "lt_06.png": "字幕：山脊之上 / 云在脚下，风在耳边",
         "lt_07.png": "字幕：登顶 / 坚持的人，风景会自己找上来",
         "03_st_sun.png": "贴纸：日出", "04_st_heart.png": "贴纸：心率", "06_st_boot.png": "贴纸：脚步",
         "05_st_water.png": "贴纸：补水", "07_st_flag.png": "贴纸：登顶旗"}
for o in sorted(ov, key=lambda x: x["start"]):
    L.append("| %s | %s | %s |" % (fmt(o["start"]), o["png"],
                                   NAMES.get(o["png"]) or DESC.get(o["png"], "")))
open(os.path.join(OUT, "镜头表.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("wrote shotlist, total %.2f, shots %d" % (TOTAL, len(shots)))
