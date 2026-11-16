
# -*- coding: utf-8 -*-
"""Windows + REPORT.md for the hike job."""
import json, os, statistics as st, collections

V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pc = {p["file"]: p for p in json.load(open(os.path.join(V,"per_clip.json"), encoding="utf-8"))}
sm = json.load(open(os.path.join(V,"summary.json"), encoding="utf-8"))
C = lambda s: "<code>" + s + "</code>"

def ranges(clip, cond, minframes=2):
    out=[]; cur=[]
    for r in tags[clip]:
        if cond(r): cur.append(r["t"])
        else:
            if len(cur)>=minframes: out.append((cur[0], round(cur[-1]+0.5,1)))
            cur=[]
    if len(cur)>=minframes: out.append((cur[0], round(cur[-1]+0.5,1)))
    return out

for clip, p in pc.items():
    p["motion_ranges"] = ranges(clip, lambda r: r["p_back"] >= 0.5 and r["p_blocked"] < 0.35 and r["p_landscape"] >= 0.5, 3)
    p["motion_score"] = round(0.4*p["mean_p_back_far"] + 0.2*p["mean_p_person"] + 0.3*p["mean_p_landscape"]
                              - 0.3*p["mean_p_blocked"] - 0.2*max(0.0, p["blur_ratio"]-0.6), 3)
json.dump(list(pc.values()), open(os.path.join(V,"per_clip.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def fr(rs, n=3):
    if not rs: return "—"
    return " / ".join("%.1f–%.1fs" % (a, b) for a, b in rs[:n])

def table(rows, cols):
    L = ["| " + " | ".join(cols) + " |", "|" + "---|"*len(cols)]
    for r in rows: L.append("| " + " | ".join(str(x) for x in r) + " |")
    return L

L=[]; A=L.append
A("# 爬山素材 CLIP 打标报告（immich-20261112_115253）\n")
A("**产物**：" + C("work/hike/vision/tags.json") + "（993 帧 / 74 镜头，0.5s 一帧）、" + C("per_clip.json") + "、本报告。模型与预处理管线复用 " + C("work/vision") + " 里的 CLIP ViT-B/32 量化模型（本地缓存，CPU 约 50 帧/秒）。\n")
A("> **t 口径**：" + C("tags.json") + " 的 " + C("t") + " = (帧文件序号 − 1) × 0.5 秒，即 " + C("sec_0001.jpg") + " 对应 t=0.0。本文区间均含首帧、止于末帧之后 0.5 秒。\n")
A("---\n")

A("## 0. 摘要\n")
A("- 全片 **%d 镜头 / %d 帧 / 约 %.0f 秒**（与素材 8 分 18 秒相符）。" % (sm["clips"], sm["frames"], sm["duration"]))
A("- **人物几乎无处不在**：%.1f%% 的帧判为“画面里有人”（p_person≥0.5），%.1f%% 的帧判为“跟拍背影”（p_back≥0.5）。这批素材本质是**跟着一个人走的跟拍素材**，所以“有人”不是筛选条件，**“背影 + 风景并存”才是运动感主力**。" % (
    100*sm["person_frames"]/sm["frames"], 100*sm["back_frames"]/sm["frames"]))
A("- **纯空镜很少**：只有 3 个镜头人物占比 <0.5（C1827 / C1828 / C1829，合计约 9 秒；且 C1827/C1828 是林间偏暗、C1829 偏糊）。真正的开阔风景要靠山顶那几个镜头，但其中多数是雾化/低细节（见 3.3），清晰可用的是 C1894 / C1882 / C1895。")
A("- **“对着地面/脚下”基本没有**：view 组的 ground_feet 只命中 **1/993 帧**，独立物理规则（无天空 + 低绿色 + 上暗下亮）也只命中 3.3%%，且这些帧多为林冠/岩壁误判。**这类废镜头不是本批素材的主要问题。**")
A("- **真正的废镜头是三类**：① 手/衣物糊镜头（p_blocked≥0.5，84 帧 = 8.5%%）；② 背包/后背怼满画面（back_close，120 帧 = 12.1%%）；③ 整体糊（客观 lapvar <0.006）。逐镜头清单见 3.1。")
A("- **结尾大远景要小心**：CLIP 大远景分最高的 C1905 / C1908 / C1907 / C1883 客观细节极低（lapvar 0.0002~0.0030、下半画面 botLap≈0.001），是**雾化/接近空白**的画面。综合“开阔 + 有实体细节”后推荐 **C1894S03 / C1882S03 / C1895S03**（lapvar 0.011~0.014、botLap 0.026~0.034）；C1905S03 可当“朦胧远山”情绪镜头。详见 3.3。\n")

A("---\n")
A("## 1. 方法\n")
A("### 1.1 标签体系（6 组 / 24 类 / 53 条提示词）\n")
A("| 组 | 类 | 用途 |")
A("|---|---|---|")
A("| presence | one / multi / none | p_person = 1−P(none)，p_people = P(multi) |")
A("| **view** | back_far / back_close / ahead_path / ground_feet / vista_wide / facing | **核心组**：6 种互斥取景，直接回答“跟拍背影 / 背包怼镜头 / 对地 / 大远景” |")
A("| occlusion | blocked / clear | p_blocked = 手 / 衣物 / 包遮住镜头 |")
A("| quality | sharp / blur / dark | p_blurry = 虚焦 + 欠曝 |")
A("| landscape | wide / subject / unclear | p_landscape = 山景 / 林间 / 远景占画面 |")
A("| scene | trail / forest / mountain / summit / sky / water / other | 主场景 |")
A("每类用 2~3 条描述句做**提示词集成**（嵌入平均再归一化），每组**独立 softmax**，避免“人物”与“遮挡”互相稀释。\n")

A("### 1.2 迭代过程（为什么改了三版）\n")
A("| 版本 | 问题 | 处理 |")
A("|---|---|---|")
A("| v1 | presence 与 occlusion 混在一组，p_closeup 有 55%% 帧 ≥0.5，与物理规则（仅 14.8%%）严重不符 | 拆成独立小组 |")
A("| v2 | 加 framing 组后 back 类吃掉 78%% 概率，p_closeup 塌到 0.04 | 改成 6 类 view 组，让“背包怼镜头 / 对地 / 空径 / 大远景 / 正面”互为竞争项 |")
A("| v3（最终） | — | view 分布：back_far 71.7%%、back_close 12.1%%、vista_wide 11.0%%、facing 3.0%%、ahead_path 2.1%%、ground_feet 0.1%% |")
A("\n该分布与素材性质（跟拍徒步 vlog）吻合，且 ground_feet 几乎不触发、与物理规则只命中 3.3%% 相互印证 —— v1 的“对地”判定是假阳性。\n")

A("### 1.3 校验\n")
A("| 校验 | 结果 |")
A("|---|---|")
A("| 内部一致性：p_person vs 另一组独立措辞的 p_human | 相关 **+0.67** |")
A("| p_landscape vs 独立措辞的 p_wide2 | 相关 **+0.70** |")
A("| p_wide_vista vs 天空占比 skyfrac | 相关 **+0.49** |")
A("| p_blurry vs 客观锐度 lapvar / 边缘密度 edge | **−0.56 / −0.65** |")
A("| p_blocked vs 肤色占比 skin / 垂直梯度 vertGrad | **+0.49 / −0.51** |")
A("| p_ground vs 物理“纯对地”规则 | 弱（+0.16）→ 该类别在本批素材几乎不存在，不用于筛选 |")
A("\n**注意**：" + C("p_blurry") + " 是相对量。这批帧客观 lapvar 中位数仅 0.017（1080p→480px + 走路抖动），p_blurry 均值 0.66 说明整体偏软，**不要用绝对值筛片，用镜头间相对比较 + lapvar**。\n")

A("---\n")
A("## 2. 全局分布\n")
A("| 指标 | mean | ≥0.5 的帧占比 |")
A("|---|---|---|")
for k, label in [("p_person","人物"),("p_people","多人"),("p_back","跟拍背影(远+近)"),("p_landscape","风景占画面"),("p_wide_vista","开阔大远景"),("p_blocked","遮挡"),("p_ground","对地"),("p_blurry","糊"),("p_clear","清晰")]:
    A("| %s | %.3f | %.1f%% |" % (label, sm["mean"][k], 100*sum(1 for c in tags for r in tags[c] if r[k]>=0.5)/sm["frames"]))
A("\n场景分布：" + "、".join("%s %d 帧(%.1f%%)" % (k, v, 100*v/sm["frames"]) for k,v in sm["scenes"].items()) + "。")
A("视角分布：" + "、".join("%s %d 帧(%.1f%%)" % (k, v, 100*v/sm["frames"]) for k,v in sm["views"].items()) + "。\n")

A("---\n")
A("## 3. 分类清单\n")
A("### 3.1 废镜头（遮挡 / 背包怼镜头 / 整体糊）\n")
A("判定（已做天空感知修正，避免把“天空多所以纹理低”的远景误判成糊）：遮挡 = p_blocked 均分 ≥0.35；背包怼镜头 = back_close 帧占比 ≥30%%；对地 = 对地帧占比 ≥20%%；整体偏糊 = lapvar<0.006 且 skyfrac<0.4；糊镜头多 = >85%% 帧 p_blurry≥0.7 且 lapvar<0.010 且 skyfrac<0.4。区间为 p_blocked≥0.5 的连续段（≥1 秒）。\n")
waste = [p for p in pc.values() if p.get("is_waste")]
waste.sort(key=lambda p: -p["mean_p_blocked"])
L.extend(table([[p["file"].replace(".mp4",""), p["frames"], p["duration"], "%.2f" % p["mean_p_blocked"], "%.2f" % p["mean_p_back_close"],
           "%.2f" % p["mean_p_ground"], "%.4f" % (p["obj_lapvar"] or 0),
           "、".join(p["flags"]),
           ("遮挡 " + fr(p["blocked_ranges"])) if p["blocked_ranges"] else "—"]
          for p in waste[:24]],
         ["镜头","帧","时长s","遮挡均分","背包怼满","对地均分","lapvar","判定标签","遮挡秒段"]))
A("\n> 完整的 74 镜头数据见 " + C("per_clip.json") + "，其中 " + C("blocked_ranges") + " 字段给出每个镜头的遮挡秒段。\n")

A("### 3.2 走路背影（运动感主力）\n")
A("排序分 = 0.4×back_far + 0.2×person + 0.3×landscape − 0.3×blocked − 0.2×max(0, 糊帧占比−0.6)。区间为“背影 + 有风景 + 无遮挡”连续 ≥1.5 秒的段。\n")
motion = sorted([p for p in pc.values() if p["mean_p_back"] >= 0.5], key=lambda p: -p["motion_score"])[:20]
L.extend(table([[p["file"].replace(".mp4",""), p["frames"], p["duration"], "%.2f" % p["mean_p_back"], "%.2f" % p["mean_p_landscape"],
           "%.2f" % p["mean_p_blocked"], "%.2f" % p["motion_score"],
           fr(p["motion_ranges"])]
          for p in motion],
         ["镜头","帧","时长s","背影均分","风景均分","遮挡均分","运动分","可用背影秒段"]))
A("\n")

A("### 3.3 山顶 / 开阔大远景（适合做结尾）\n")
ending = sorted(pc.values(), key=lambda p: -p["ending_score"])[:14]
A("排序分 = 0.45×大远景 + 0.30×风景 + 0.25×客观细节（botLap 饱和到 0.02）。**加客观细节列是必须的**：第一版只按 CLIP 大远景分排，前几名（C1907 / C1908 / C1883）实际上 lapvar 只有 0.0002~0.0025、下半个画面细节 botLap≈0.001，是雾化/接近空白的画面，直接当结尾会“发灰发闷”。\n")
L.extend(table([[p["file"].replace(".mp4",""), p["frames"], p["duration"], "%.2f" % p["mean_p_wide_vista"],
           "%.0f%%" % (100*p["vista_ratio"]), "%.2f" % p["mean_p_landscape"], "%.4f" % (p["obj_lapvar"] or 0),
           "%.4f" % (p["obj_botLap"] or 0), "%.3f" % (p["obj_colorful"] or 0), "%.2f" % p["ending_score"],
           "、".join(x for x in p["flags"] if x in ("低细节/雾化","纯天空/低内容","大远景/山顶")) or "—"]
          for p in ending],
         ["镜头","帧","时长s","大远景均分","远景帧占比","风景均分","lapvar","botLap","色彩度","结尾分","注意"]))
A("\n**结论**：真正“开阔又不糊”的结尾候选是 **C1894S03 / C1882S03 / C1895S03**（lapvar 0.011~0.014、botLap 0.026~0.034，画面有实体细节）；")
A("C1905S03 的 CLIP 大远景分最高（0.62）但客观是低反差雾化远山（lapvar 0.0030、色彩度 0.085），适合做“朦胧远山”情绪镜头、不适合当清晰大远景；")
A("**C1907 / C1908 / C1883 几乎空白（纯天空或重度雾化），不建议做结尾**。\n")

A("### 3.4 几乎没有人物的镜头（纯空镜候选）\n")
empty = sorted(pc.values(), key=lambda p: p["mean_p_person"])
L.extend(table([[p["file"].replace(".mp4",""), p["frames"], p["duration"], "%.2f" % p["mean_p_person"], "%.2f" % p["mean_p_landscape"],
           "%.2f" % p["mean_p_wide_vista"], "%.2f" % p["mean_p_blocked"], "%.4f" % (p["obj_lapvar"] or 0), p["dominant_scene"],
           ", ".join(p["flags"])]
          for p in empty[:12]],
         ["镜头","帧","时长s","人物均分","风景均分","大远景均分","遮挡均分","lapvar","场景","标签"]))
A("\n> 只有 C1827 / C1828 / C1829 三支人物占比 <0.5，且 C1827/C1828 林间偏暗、C1829 偏糊；**这批素材没有高质量纯空镜**，空镜需求建议用 3.3 里“开阔 + 有细节”的 C1894 / C1882 / C1895，而不是雾化的 C1907/C1908。\n")

A("---\n")
A("## 4. 全部 74 个镜头\n")
A("按运动分降序。人物 = p_person 均分；背影 = p_back 均分；风景 = p_landscape 均分；远景 = p_wide_vista 均分；遮挡 = p_blocked 均分；糊 = p_blurry 均分。\n")
allrows = []
for p in sorted(pc.values(), key=lambda p: -p["motion_score"]):
    allrows.append([p["file"].replace(".mp4",""), p["frames"], p["duration"],
                    "%.2f" % p["mean_p_person"], "%.2f" % p["mean_p_back"], "%.2f" % p["mean_p_landscape"],
                    "%.2f" % p["mean_p_wide_vista"], "%.2f" % p["mean_p_blocked"], "%.2f" % p["mean_p_blurry"],
                    p["dominant_scene"], p["dominant_view"],
                    " ".join("⚠" + f for f in p["flags"] if f in ("遮挡","背包怼镜头","对地","糊镜头多","整体偏糊"))])
L.extend(table(allrows, ["镜头","帧","时长","人物","背影","风景","远景","遮挡","糊","场景","主视角","警告"]))
A("\n")

A("---\n")
A("## 5. 使用建议\n")
A("1. **开场 / 中段运动感**：用 3.2 节运动分高的镜头（C1884 / C1886 / C1899 / C1895 / C1898 / C1877 等），它们“背影 + 风景 + 少遮挡”三者兼备；单镜头 2~19 秒，可直接按 3~5 秒截取 3.2 节给出的现成秒段。")
A("2. **结尾**：用 **C1894S03（6.5s）/ C1882S03（6.5s）/ C1895S03（5.5s）** —— 开阔且画面有实体细节（lapvar 0.011~0.014、botLap 0.026~0.034）；想要“朦胧远山”氛围可用 C1905S03（13s，低反差发灰）；**C1907 / C1908 / C1883 接近空白，不建议做结尾**。")
A("3. **剔除**：3.1 节的废镜头。特别提醒 **C1862S03**：人物/风景分看着高，但 93%% 的帧 p_blocked≥0.5、背包怼满画面（back_close 0.73），实际基本不可用，别被高分误导。")
A("4. **过渡**：C1895 / C1894 / C1881 的 vista 帧可做 2 秒空镜过渡。")
A("5. 遮挡秒段精度 0.5 秒，全部在 " + C("per_clip.json") + " 的 " + C("blocked_ranges") + "；可用背影段在 " + C("motion_ranges") + "；远景段在 " + C("vista_ranges") + "。\n")

A("---\n")
A("## 6. 局限\n")
A("1. 团队里没人能直接看图，结论来自 CLIP + 客观像素统计两条独立证据链，方向一致（见 1.3），但不是人眼确认。带 ⚠ 的镜头建议抽 1~2 帧肉眼复核。")
A("2. **p_person 几乎饱和（97.9%%）**，不能用来排序“有多有人”，只能用来找“几乎没人”的少数镜头；动作感排序请用 3.2 的运动分。")
A("3. **p_ground 在本批素材几乎不触发（0.1%%）**，与物理规则（3.3%% 且多为林冠误判）一致 → 这批素材没有明显“对地/对脚”镜头。若剪辑师看到某段确实在拍地，以人眼为准。")
A("4. “背包怼镜头”（back_close）可靠度中等：它与“近距离背影”语义接近，12%% 的帧处于边界，可能有 1~2 帧误判。")
A("5. p_blurry 是相对量，1080p→480px 的帧客观偏软（lapvar 中位 0.017），不要当绝对清晰度标准。")
A("6. 0.5 秒抽帧，遮挡/可用段的边界精度为 ±0.5 秒。\n")

A("---\n")
A("## 7. 产物\n")
A("| 文件 | 内容 |")
A("|---|---|")
A("| " + C("tags.json") + " | 993 帧，每帧：t、p_person、p_people、p_nobody、p_back、p_back_far、p_back_close、p_facing、p_trail_ahead、p_ground(=p_closeup)、p_wide_vista、p_landscape、p_clear、p_blocked、p_blurry、scene、scene_p、view、p_landscape_pct |")
A("| " + C("per_clip.json") + " | 74 镜头聚合：mean p_person / p_landscape / p_blocked、主场景、视角、比值、客观指标、flags、blocked_ranges / motion_ranges / vista_ranges、motion_score |")
A("| " + C("pixstats.json") + " / " + C("aux.json") + " | 客观像素统计 / 第二组独立措辞的 CLIP 校验信号 |")
A("| " + C("tag_hike.mjs") + " / " + C("pixstats_hike.py") + " / " + C("build_hike.py") + " / " + C("report_hike.py") + " | 打标 / 客观统计 / 聚合 / 报告脚本 |")
A("| " + C("_frames_fallback/") + " | 我自备的同规格抽帧（74 镜头 993 帧），与 footage-analyst 产物数量一致，仅作备份 |")
A("\n")

txt = "\n".join(L).replace("%%", "%")
open(os.path.join(V, "REPORT.md"), "w", encoding="utf-8").write(txt)
print("REPORT.md written", os.path.getsize(os.path.join(V,"REPORT.md")), "bytes")
print("waste clips:", len(waste), "| motion:", len(motion), "| ending:", len(ending), "| empty:", len(empty))
