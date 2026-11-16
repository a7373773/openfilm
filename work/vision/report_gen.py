
# -*- coding: utf-8 -*-
import json, os, statistics as st, collections

V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pix = json.load(open(os.path.join(V,"pixstats.json"), encoding="utf-8"))
aux = json.load(open(os.path.join(V,"aux.json"), encoding="utf-8"))
pf = json.load(open(os.path.join(V,"per_file.json"), encoding="utf-8"))
cands = json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8"))
sm = json.load(open(os.path.join(V,"summary.json"), encoding="utf-8"))
C = lambda s: "<code>" + s + "</code>"

def _seg(f, cur):
    mean = sum(r["p_blocked"] for r in cur)/len(cur)
    cand = [("手 hand", sum(r["p_hand"] for r in cur)/len(cur)),
            ("衣物 fabric", sum(r["p_fabric"] for r in cur)/len(cur)),
            ("地面朝下 closeup", sum(r["p_closeup"] for r in cur)/len(cur))]
    dom = max(cand, key=lambda z: z[1])[0]
    return dict(file=f, s=cur[0]["t"], e=cur[-1]["t"], d=len(cur), mean=mean, dom=dom)

def segs(cond, minlen=2):
    out=[]
    for f in sorted(tags):
        cur=[]
        for r in tags[f]:
            if cond(r):
                cur.append(r)
            else:
                if len(cur) >= minlen: out.append(_seg(f, cur))
                cur=[]
        if len(cur) >= minlen: out.append(_seg(f, cur))
    return out

spec = segs(lambda r: r["p_blocked"]>0.5)
strict = segs(lambda r: max(r["p_hand"], r["p_fabric"])>0.5)
dec = sm["deciles"]; decb = sm["deciles_p_blocked"]
L = []

L.append("# CLIP 零样本打标报告 —— 遮挡帧识别 / 纯风景候选\n")
L.append("**产物目录**：" + C("work/vision/") + "　|　**数据**：24 个 mp4 → 2603 帧（1 fps，480px 宽，共 2605.1 秒）　|　**模型**：CLIP ViT-B/32（Xenova ONNX 量化版，本地缓存，CPU 推理 62 帧/秒）\n")
L.append("---\n")

L.append("## 0. 摘要（先看这里）\n")
L.append("- **全局 p_landscape 很低**：mean=%.3f，中位数 %.3f，只有 %d/%d 帧（%.1f%%）p_landscape≥0.5。这批运动相机素材本身偏灰/偏软/逆光，**绝对阈值不可靠，必须用文件内相对排序**。" % (
    sm["mean_p_landscape"], dec["p50"], sm["landscape_ge_05"], sm["total_frames"], 100*sm["landscape_ge_05"]/sm["total_frames"]))
L.append("- **6 个文件整体是废片**（landscape_ratio<0.05，共 650 秒）：REC-0025-A、REC-0027-A、REC-0024-A、REC-0026-A、REC-0002-A、REC-0019-A。其中 5 个的主因是**镜头朝下对着地面/路面**（p_closeup 主导），只有 REC-0002-A 是手+衣物遮挡主导。")
L.append("- **最好用**：REC-0016-A（ratio 0.76）、REC-0021-A（0.44）、REC-0007-A（0.40）、REC-0012-A（0.36）、REC-0006-A（0.31）。")
_spec_n, _spec_s = len(spec), sum(s["d"] for s in spec)
_strict_n, _strict_s = len(strict), sum(s["d"] for s in strict)
L.append("- **遮挡秒区间**：按口径 " + C("max(p_hand,p_fabric,p_closeup)>0.5") + " 连续≥2s → **%d 段 / %d 秒**；若只算真正的手/衣物遮挡 " % (_spec_n, _spec_s)
         + C("max(hand,fabric)>0.5") + " → **%d 段 / %d 秒**（差集 %d 秒基本全是\"朝下拍地面\"）。" % (_strict_n, _strict_s, _spec_s - _strict_s))
L.append("- **候选区间**（连续≥3s、mean p_landscape ≥ 本文件中位数+0.10、p_blocked<0.35）：**%d 段 / %d 秒**，其中 %d 段被标为 " % (sm["candidates"], sm["candidate_secs"], sm["candidates_blank_suspect"]) + C("blank_sky_suspect") + "（疑似纯天空/过曝、画面无细节），建议剔除或只当空镜。")
L.append("- **⚠ t 对齐口径**：tags.json 里 " + C("t") + " 是 **1-based**，对应 " + C("frames/sec_(t).jpg") + "；与 " + C("work/analysis/metrics.json") + " 的 0-based t 对齐需 **t_metrics = t_tags − 1**。\n")

L.append("---\n")
L.append("## 1. 方法与运行环境\n")
L.append("### 1.1 管线\n")
L.append("1. 模型：" + C("Xenova/clip-vit-base-patch32") + "（CLIP ViT-B/32，ONNX int8 量化，153 MB），从 **hf-mirror.com** 用 curl 预下载到 " + C("work/vision/cache/") + "，**运行时零网络**。")
L.append("2. 解码与预处理：" + C("jpeg-js") + " 解码 JPEG → 双线性缩放到短边 224 → 中心裁剪 224×224 → (x−mean)/std（CLIP 官方均值/方差）→ float32 CHW。**完全不依赖 sharp**。")
L.append("3. 提示词集成（prompt ensembling）：每一类用 2~5 条英文描述句，各自取文本嵌入后**平均再归一化**，避免单句提示词导致的概率平坦。")
L.append("4. 主标签组（5 类，14 条提示词）：" + C("landscape") + " 风景 / " + C("hand") + " 手挡镜头 / " + C("fabric") + " 衣物包遮挡 / " + C("blurry") + " 模糊黑暗不可读 / " + C("ground") + " 地面墙面贴脸。")
L.append("5. 场景标签组（9 类，18 条提示词）：mountain / water / forest / sunset / road / city / snow / beach / night。")
L.append("6. **p_blocked 定义（按 lead 要求）**：" + C("max(p_hand, p_fabric, p_closeup)") + "，**不含 p_blurry** —— 避免雾天/逆光的正常风景被误判。tags.json 同时保留 p_blurry 供单独参考。")
L.append("7. 辅助信号组（4 类，9 条提示词，" + C("aux.json") + "）：clear_scenery 有细节的清晰风景 / empty_sky 纯天空 / washed 过曝洗白低对比 / obstruction 手衣物模糊遮挡。用途是识别\"p_landscape 高但其实是过曝天空\"的假阳性。")
L.append("8. 独立客观统计（" + C("pixstats.json") + "，Python+numpy/Pillow）：亮度、对比度、Laplacian 方差（锐度）、边缘密度、色彩丰富度、饱和度、暗部/亮部占比、肤色占比、顶/底半区亮度与纹理、天空占比、植被占比、平坦块占比。用于交叉校验与排序辅助。\n")

L.append("### 1.2 环境踩坑（供复现）\n")
L.append("- " + C("npm i @xenova/transformers@2.17.2") + " 直接失败：依赖 " + C("sharp") + " 的 postinstall 要去 **github.com** 下 libvips（超时）。解决：" + C("npm i --ignore-scripts --no-audit --no-fund") + "，并把 " + C("node_modules/sharp") + " 替换成 stub（sharp 会被 @xenova/transformers 顶层 require，但我们的路径完全不用它）。")
L.append("- hf-mirror 的 **HEAD 请求会偶发失败**，GET 正常；transformers.js 内部 fetch 无重试，所以改成 curl " + C("--retry 3 --retry-all-errors -C -") + " 预下载模型（config.json / preprocessor_config.json / tokenizer.json / tokenizer_config.json / special_tokens_map.json / vocab.json / merges.txt / onnx/model_quantized.onnx），再设 " + C("env.allowRemoteModels=false; env.allowLocalModels=true; env.localModelPath=缓存目录") + "。")
L.append("- " + C("onnxruntime-node@1.14.0") + " 的 win32-x64 原生库**随 npm 包自带**，无需额外下载，Node v24 下 napi-v3 正常加载。\n")

L.append("---\n")
L.append("## 2. 校验记录（为什么相信这些概率）\n")
L.append("### 2.1 合成图 ground truth（验证判别力）\n")
L.append("第一版单提示词的概率是\"平的\"（所有帧 p_blur≈0.86，明显异常）。改用合成图对照，确认判别力正常：\n")
L.append("| 输入图 | 应命中的标签 | softmax |")
L.append("|---|---|---|")
L.append("| 8×8 棋盘 | a checkerboard pattern | **0.963** |")
L.append("| 纯白 | plain white screen | **0.690** |")
L.append("| 随机噪声 | colorful random noise | **0.625** |")
L.append("| 纯黑 | plain black screen | **0.594** |\n")
L.append("说明模型本身没问题，早期平坦是提示词太少 + 5 类互相稀释导致；提示词集成后 p_landscape 拉开到 0.002~0.948。\n")

L.append("### 2.2 与独立像素统计交叉验证（全量 2603 帧）\n")
L.append("| 相关系数 | p_clear_scenery | p_blank（纯天空/过曝） | p_landscape | p_blocked |")
L.append("|---|---|---|---|---|")
L.append("| 边缘密度 edge | **+0.58** | **−0.51** | −0.24 | +0.10 |")
L.append("| Laplacian 方差 lapvar | **+0.40** | **−0.38** | −0.19 | +0.01 |")
L.append("| 天空占比 skyfrac | −0.33 | **+0.53** | **+0.47** | **−0.41** |")
L.append("| 平坦块占比 flatfrac | **−0.44** | **+0.55** | +0.43 | −0.27 |")
L.append("| 底半区细节 botLap | **+0.37** | −0.29 | −0.10 | −0.10 |")
L.append("\n方向全部符合预期：\"清晰风景\"跟着边缘/纹理走，\"过曝天空\"跟着天空/平坦/低对比走，\"遮挡\"跟着低天空占比走。这是本报告可信度的主要依据（因为团队里没人能直接看图）。\n")

L.append("### 2.3 已知可疑文件抽查：REC-0004-A 前 20 秒\n")
L.append("lead 提示该文件前 20 秒锐度偏低。独立像素统计与 CLIP 判定一致：\n")
L.append("| t | p_landscape | p_blocked | lapvar | skyfrac | 判定 |")
L.append("|---|---|---|---|---|---|")
for t in range(1, 21):
    r = next((x for x in tags["REC-0004-A.mp4"] if x["t"] == t), None)
    p = pix["REC-0004-A"].get(str(t))
    if not r or not p: continue
    verdict = "遮挡/糊白" if r["p_blocked"] > 0.5 else ("尚可" if r["p_landscape"] >= 0.4 else "平庸")
    L.append("| %d | %.2f | %.2f | %.4f | %.2f | %s |" % (t, r["p_landscape"], r["p_blocked"], p["lapvar"], p["skyfrac"], verdict))
L.append("\n结论：**t=1~4 确实是过曝/糊白的废秒**（p_blocked 0.85~0.90，lapvar 仅 0.002~0.003，skyfrac 0.77~0.95 —— 几乎全白无细节）。t=5 之后 CLIP 给的中等分（0.4~0.8）与极低的 lapvar（0.004 级）矛盾，说明这条片子整体\"软/糊\"：CLIP 按构图/色彩觉得像风景，但物理锐度很差。**建议这条片子当备选，不要当主镜头。**\n")

L.append("### 2.4 多文件抽查（3 个可疑文件 + 1 个对照文件）\n")
L.append("除 REC-0004-A 外，再对 landscape_ratio 最低的 2 个文件和最好的 1 个文件抽样，检查 CLIP 与客观统计是否互相印证：\n")
L.append("| 文件 | t | p_landscape | p_blocked | p_closeup | p_blurry | lapvar | skyfrac | botLap | 判读 |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
def _verdict(r, p):
    if r["p_blocked"] > 0.5: return "遮挡（%s）" % ("朝下" if r["p_closeup"] >= max(r["p_hand"], r["p_fabric"]) else "手/衣物")
    if r["p_landscape"] >= 0.5 and p["botLap"] > 0.015: return "清晰风景"
    if r["p_landscape"] >= 0.5: return "风景但缺细节"
    return "平庸/不可用"
for f in ["REC-0024-A.mp4", "REC-0025-A.mp4", "REC-0016-A.mp4", "REC-0002-A.mp4"]:
    rows = tags[f]; n = len(rows)
    for t in sorted(set([1, max(1, n//3), max(1, 2*n//3), n])):
        r = next((x for x in rows if x["t"] == t), None)
        p = pix[f.replace(".mp4","")].get(str(t))
        if not r or not p: continue
        L.append("| %s | %d | %.2f | %.2f | %.2f | %.2f | %.4f | %.2f | %.4f | %s |" % (
            f.replace(".mp4",""), t, r["p_landscape"], r["p_blocked"], r["p_closeup"], r["p_blurry"],
            p["lapvar"], p["skyfrac"], p["botLap"], _verdict(r, p)))
L.append("\n读法：REC-0024-A / REC-0025-A 几乎每一采样点都是 p_closeup 主导的\"朝下拍地面\"（lapvar 极低、botLap 接近 0），与 landscape_ratio≈0 一致；")
L.append("REC-0016-A 作为对照，采样点普遍 p_landscape 高、botLap 有实质细节，与 ratio=0.76 一致；REC-0002-A 则是手+衣物（p_hand/p_fabric）主导，与其它 5 个\"朝下\"片子成因不同。\n")

L.append("---\n")
L.append("## 3. 全局分布与相对阈值建议\n")
L.append("### 3.1 p_landscape 十分位（n=%d 帧）\n" % sm["total_frames"])
L.append("| 统计量 | p10 | p25 | p50 | p75 | p90 | mean |")
L.append("|---|---|---|---|---|---|---|")
L.append("| p_landscape | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f |" % (dec["p10"], dec["p25"], dec["p50"], dec["p75"], dec["p90"], sm["mean_p_landscape"]))
L.append("| p_blocked | %.3f | %.3f | %.3f | %.3f | %.3f | — |" % (decb["p10"], decb["p25"], decb["p50"], decb["p75"], decb["p90"]))
L.append("\np_landscape ≥0.5：%d 帧（%.1f%%）；≥0.3：%d 帧（%.1f%%）。文件内 landscape_ratio 的中位数只有 %.3f。\n" % (
    sm["landscape_ge_05"], 100*sm["landscape_ge_05"]/sm["total_frames"], sm["landscape_ge_03"], 100*sm["landscape_ge_03"]/sm["total_frames"],
    st.median([r["landscape_ratio"] for r in pf])))

L.append("### 3.2 建议的相对阈值口径\n")
L.append("| 用途 | 建议口径 |")
L.append("|---|---|")
L.append("| 单帧\"值得当主镜头\" | 全局 p_landscape_pct ≥ 0.85 **且** 文件内 p_landscape ≥ 本文件 p75 |")
L.append("| 单帧\"可用\" | 全局 p_landscape_pct ≥ 0.70 **且** 文件内 p_landscape ≥ 本文件中位数 |")
L.append("| 直接弃用 | 全局 p_landscape_pct ≤ 0.25 或 p_blocked > 0.5 |")
L.append("| 整文件废片 | landscape_ratio < 0.05（见第 4 节的 6 个文件） |")
L.append("\ntags.json 每帧已带 " + C("p_landscape_pct") + "（全局经验分位 0~1）与 " + C("p_landscape_rel") + "（相对本文件中位数的差值），可直接用于相对排序。\n")

L.append("---\n")
L.append("## 4. 每个文件一览（24 个文件）\n")
L.append("按 landscape_ratio 升序排列（越低越废）。cand 列 = 该文件入选候选区间的总秒数。\n")
L.append("| 文件 | 帧数 | landscape_ratio | mean p_landscape | median p_landscape | mean p_blocked | mean p_blurry | 遮挡秒 | 候选秒 | 主场景 |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for r in sorted(pf, key=lambda r: r["landscape_ratio"]):
    L.append("| %s | %d | **%.2f** | %.3f | %.3f | %.3f | %.3f | %ds | %ds | %s |" % (
        r["file"].replace(".mp4", ""), r["frames"], r["landscape_ratio"], r["mean_p_landscape"], r["median_p_landscape"],
        r["mean_p_blocked"], r["mean_p_blurry"], r["blocked_secs"], r["candidate_secs"], r["top_scene"]))
L.append("\n")

L.append("---\n")
L.append("## 5. 遮挡秒区间\n")
L.append("### 5.1 口径 A（lead 指定，报告主口径）：" + C("max(p_hand, p_fabric, p_closeup) > 0.5") + "，连续 ≥2 秒\n")
L.append("共 **%d 段 / %d 秒**（占全素材 %.1f%%）。\"主因\"列是该段内三类里平均概率最高的一类。\n" % (
    len(spec), sum(s["d"] for s in spec), 100*sum(s["d"] for s in spec)/sm["total_frames"]))
dom_cnt = collections.Counter(s["dom"] for s in spec)
L.append("主因分布：手 hand %d 段 / 衣物 fabric %d 段 / 地面朝下 closeup %d 段。\n" % (
    dom_cnt.get("手 hand",0), dom_cnt.get("衣物 fabric",0), dom_cnt.get("地面朝下 closeup",0)))
by_file = collections.defaultdict(list)
for s in spec: by_file[s["file"]].append(s)
L.append("| 文件 | 段数 | 总秒 | 区间（秒，1-based，含首尾） |")
L.append("|---|---|---|---|")
for f in sorted(by_file):
    ss = by_file[f]
    rng = "、".join("%d–%d%s" % (s["s"], s["e"], "" if s["dom"].startswith("地面") else "(%s)" % s["dom"].split()[0]) for s in ss)
    L.append("| %s | %d | %d | %s |" % (f.replace(".mp4",""), len(ss), sum(s["d"] for s in ss), rng))
L.append("\n> 未标括号的段主因是\"地面朝下 closeup\"；标 (手)/(衣物) 的是真正的手/衣物遮挡。\n")

L.append("### 5.2 口径 B（只看真手/衣物遮挡）：" + C("max(p_hand, p_fabric) > 0.5") + "，连续 ≥2 秒\n")
L.append("共 **%d 段 / %d 秒**。如果剪辑只需要剔除\"手/衣服糊住镜头\"，用这一份；差集 634 秒是朝下拍地面，多数发生在运动/骑行过程中，未必需要全删。\n" % (len(strict), sum(s["d"] for s in strict)))
L.append("| 文件 | 区间（秒，1-based） |")
L.append("|---|---|")
for f in sorted(set(s["file"] for s in strict)):
    ss = [s for s in strict if s["file"] == f]
    L.append("| %s | %s |" % (f.replace(".mp4",""), "、".join("%d–%d" % (s["s"], s["e"]) for s in ss)))
L.append("\n")

L.append("---\n")
L.append("## 6. 候选区间（纯风景段）\n")
L.append("### 6.1 入选规则（lead 指定）\n")
L.append("- 连续 ≥3 秒；")
L.append("- 该区间 mean p_landscape ≥ **该文件自身 p_landscape 中位数 + 0.10**（相对口径，避免绝对阈值失效）；")
L.append("- 该区间 mean p_blocked < 0.35。\n")
L.append("共 **%d 段 / %d 秒**。每段附客观统计：skyfrac 天空占比、flatfrac 平坦无细节块占比、botLap 底半区锐度、lapvar 全图锐度、colorful 色彩丰富度、edge 边缘密度、greenfrac 植被占比，以及 detail_score（0~1 综合细节分）与 blank_sky_suspect（疑似纯天空/过曝）。\n" % (sm["candidates"], sm["candidate_secs"]))
L.append("### 6.2 全表（按 mean p_landscape 降序）\n")
L.append("| # | 文件 | 起–止(s) | 时长 | mean L | mean blk | 场景(scene_p) | detail | 纯天空可疑 |")
L.append("|---|---|---|---|---|---|---|---|---|")
for i, c in enumerate(cands, 1):
    L.append("| %d | %s | %d–%d | %ds | %.3f | %.3f | %s(%.2f) | %.2f | %s |" % (
        i, c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["dur"], c["mean_p_landscape"], c["mean_p_blocked"],
        c["scene"], c["scene_p"], c["detail_score"], "⚠ 是" if c["blank_sky_suspect"] else ""))
L.append("\n")

L.append("### 6.3 推荐优先使用的候选（长度 × 细节综合排序，排除纯天空可疑）\n")
L.append("| 文件 | 起–止(s) | 时长 | mean L | 场景 | detail | 备注 |")
L.append("|---|---|---|---|---|---|---|")
good = [c for c in cands if not c["blank_sky_suspect"]]
good.sort(key=lambda c: -(c["mean_p_landscape"]*0.5 + c["detail_score"]*0.5))
for c in good[:15]:
    note = "长镜头，首推" if c["dur"] >= 15 else ("细节很足" if c["detail_score"] >= 0.9 else "")
    L.append("| %s | %d–%d | %ds | %.3f | %s | %.2f | %s |" % (
        c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["dur"], c["mean_p_landscape"], c["scene"], c["detail_score"], note))
L.append("\n### 6.4 被标为\"疑似纯天空/过曝\"的候选（%d 段，建议只当空镜或剔除）\n" % sm["candidates_blank_suspect"])
L.append("| 文件 | 起–止(s) | mean L | skyfrac | botLap | p_blank |")
L.append("|---|---|---|---|---|---|")
for c in [x for x in cands if x["blank_sky_suspect"]]:
    s = c["stats"]
    L.append("| %s | %d–%d | %.3f | %.2f | %.4f | %.2f |" % (c["file"].replace(".mp4",""), c["start_t"], c["end_t"], c["mean_p_landscape"], s["skyfrac"], s["botLap"], s["p_blank"]))
L.append("\n")

L.append("---\n")
L.append("## 7. 局限与不确定度（必读）\n")
L.append("1. **没人能直接看图**，所有结论来自 CLIP + 客观像素统计两条独立证据链，两者方向一致（见 2.2），但都不是\"人眼确认\"。凡本报告标 ⚠ 的位置，建议剪辑师抽 1~2 帧肉眼扫一下再决定。")
L.append("2. **p_landscape 绝对分偏低且偏向\"亮、平、天空多\"**：与 skyfrac 相关 +0.47、与 lapvar 相关 −0.19。所以\"p_landscape 高\"≈\"构图像风景且不暗\"，不等于\"画面好看/清晰\"。因此本报告所有取舍都优先用**文件内相对分位 + detail_score**，并把疑似纯天空单独标出。")
L.append("3. **p_blocked 口径敏感度极大**（720s vs 86s）：这批素材里\"镜头朝下拍地面\"占比很高，朝下镜头在语义上既像\"地面贴脸\"也像\"路面风景\"。road 场景的帧里只有 3% 的 p_closeup>0.35，说明模型没有把\"道路风景\"大面积误判成\"地面贴脸\"，但**边界段的判定仍可能有 ±1~2 秒抖动**。")
L.append("4. **t 是 1-based**（sec_0001.jpg = t 1）。与 metrics.json 的 0-based t 对齐：t_metrics = t_tags − 1。区间 [start_t, end_t] 含首尾。")
L.append("5. 量化 int8 模型 + 480px 低分辨率帧：概率分辨率有限，不要解读小数点后第三位。相对排序可靠，绝对值仅供大致参考。")
L.append("6. 24 个文件里有 8 个短片段（REC-0004/0013/0014/0016/0019/0022/0023/0027），样本少，其\"文件内中位数\"统计噪声更大。\n")

L.append("---\n")
L.append("## 8. 产物清单\n")
L.append("| 文件 | 内容 |")
L.append("|---|---|")
L.append("| " + C("tags.json") + " | 每帧标签。键为 REC-XXXX-A.mp4，值按 t 升序：t, p_landscape, p_blocked, p_hand, p_fabric, p_closeup, p_blurry, scene, scene_p, p_landscape_pct, p_landscape_rel |")
L.append("| " + C("per_file.json") + " | 每文件聚合：mean/median p_landscape、mean p_blocked、mean p_blurry、landscape_ratio、blocked_ratio、blocked_secs、candidate_secs、主场景等 |")
L.append("| " + C("candidates.json") + " | 候选区间（规则见 6.1），含场景、客观统计、detail_score、blank_sky_suspect |")
L.append("| " + C("pixstats.json") + " | 每帧客观像素统计（亮度/锐度/边缘/天空/植被/平坦度等） |")
L.append("| " + C("aux.json") + " | 第二组 CLIP 辅助信号：p_clear_scenery / p_empty_sky / p_washed / p_obstruction / p_blank |")
L.append("| " + C("summary.json") + " | 全局分布、遮挡区间、候选、每文件汇总 |")
L.append("| " + C("tag_frames.mjs") + " / " + C("aux_tags.mjs") + " | 主打标 / 辅助信号脚本 |")
L.append("| " + C("pixstats.py") + " / " + C("analyze.py") + " / " + C("build_final.py") + " / " + C("report_gen.py") + " | 客观统计与聚合脚本 |")
L.append("| " + C("cache/") + " | CLIP 模型本地缓存（153 MB，运行时零网络） |")
L.append("\n")

open(os.path.join(V, "REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
print("REPORT.md written:", os.path.getsize(os.path.join(V,"REPORT.md")), "bytes")
print("blocked:", len(spec), sum(s["d"] for s in spec), "| strict:", len(strict), sum(s["d"] for s in strict))
print("candidates:", len(cands), "| blank:", sum(1 for c in cands if c["blank_sky_suspect"]))
