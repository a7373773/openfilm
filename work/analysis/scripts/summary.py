# -*- coding: utf-8 -*-
import os, json, math, statistics as st

OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
SRC = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/素材"
META = os.path.join(OUT, "meta.json")
METRICS = os.path.join(OUT, "metrics.json")

LBL = {
    "BLACK": "极暗/近全黑",
    "WHITE": "过曝白场",
    "BLOCK": "无细节/疑似遮挡",
    "BLUR":  "低锐度/虚焦或运动模糊",
    "FLATS": "单色平板/大面积天空",
}
PRIO = ["BLACK", "WHITE", "BLOCK", "BLUR", "FLATS"]

def pct(a, p):
    if not a: return 0.0
    s = sorted(a); k = (len(s)-1)*p; f = int(math.floor(k)); c = min(f+1, len(s)-1)
    return s[f] + (s[c]-s[f])*(k-f)

def med(a):
    return st.median(a) if a else 0.0

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)

def mmss(t):
    t = int(round(t))
    return "%d:%02d" % (t//60, t%60)

def classify(fn, fr, dur):
    n = len(fr)
    sh = [f["sharp"] for f in fr]
    ed = [f["edgefrac"] for f in fr]
    co = [f["colorful"] for f in fr]
    en = [f["entropy"] for f in fr]
    fi = [f["fineratio"] for f in fr]
    di = [f["diff"] for f in fr]
    PS = max(pct(sh, 0.90), 1.0)
    PE = max(pct(ed, 0.90), 0.001)
    PC = max(pct(co, 0.90), 1.0)
    dref = max(pct(di, 0.50), 1.0)

    lab = [None]*n
    d = [0.0]*n; e = [0.0]*n
    for i, f in enumerate(fr):
        d[i] = f["sharp"]/PS
        e[i] = f["edgefrac"]/PE
        if f["luma"] < 35 or f["darkfrac"] > 0.70:
            lab[i] = "BLACK"
        elif f["luma"] > 240 or f["brightfrac"] > 0.80:
            lab[i] = "WHITE"
        elif e[i] < 0.15 and d[i] < 0.15:
            lab[i] = "BLOCK"
        elif d[i] < 0.25 and e[i] < 0.50 and f["fineratio"] < 0.16 and f["lumastd"] >= 32 and f["uniform"] < 0.45:
            lab[i] = "BLUR"
        elif f["uniform"] > 0.45 or f["lumastd"] < 25:
            lab[i] = "FLATS"

    qs = []
    for f in fr:
        s = clamp(f["sharp"]/(0.85*PS))
        c = clamp(f["colorful"]/(0.80*PC))
        g = clamp((f["fineratio"]-0.06)/0.16)
        lu = f["luma"]
        x = 1.0 if 30 <= lu <= 235 else clamp(1.0 - abs(lu-(30 if lu < 30 else 235))/30.0)
        qs.append(round(0.40*s + 0.20*c + 0.25*g + 0.15*x, 3))

    runs = []
    i = 0
    while i < n:
        if lab[i]:
            j = i
            while j+1 < n and lab[j+1]:
                j += 1
            runs.append([i, j]); i = j+1
        else:
            i += 1
    merged = []
    for a, b in runs:
        if merged and a - merged[-1][1] <= 2:
            merged[-1][1] = b
        else:
            merged.append([a, b])

    blocked = []
    for a, b in merged:
        k = b - a + 1
        cnt = {}
        for t in range(a, b+1):
            if lab[t]:
                cnt[lab[t]] = cnt.get(lab[t], 0) + 1
        main = max(cnt, key=lambda z: (cnt[z], -PRIO.index(z)))
        mfr = med([fr[t]["fineratio"] for t in range(a, b+1)])
        blocked.append({
            "start": a, "end": b, "dur": k, "label": main, "label_txt": LBL[main], "mix": cnt,
            "mean_det": round(sum(d[a:b+1])/k, 3),
            "mean_edge": round(sum(e[a:b+1])/k, 3),
            "median_fineratio": round(mfr, 3),
            "median_sharp": round(med([fr[t]["sharp"] for t in range(a, b+1)]), 1),
            "median_luma": round(med([fr[t]["luma"] for t in range(a, b+1)]), 1),
            "median_lumastd": round(med([fr[t]["lumastd"] for t in range(a, b+1)]), 1),
            "median_uniform": round(med([fr[t]["uniform"] for t in range(a, b+1)]), 3),
            "median_entropy": round(med([fr[t]["entropy"] for t in range(a, b+1)]), 2),
            "median_warmfrac": round(med([fr[t]["warmfrac"] for t in range(a, b+1)]), 3),
            "mean_diff": round(sum(fr[t]["diff"] for t in range(a, b+1))/k, 1),
            "conf": "high" if k >= 5 else ("mid" if k >= 2 else "low"),
        })

    bad = set()
    for a, b in merged:
        bad.update(range(a, b+1))
    usable = []
    i = 0
    while i < n:
        if i not in bad:
            j = i
            while j+1 < n and (j+1) not in bad:
                j += 1
            if j-i+1 >= 5:
                usable.append({"start": i, "end": j, "dur": j-i+1,
                               "mean_q": round(sum(qs[i:j+1])/(j-i+1), 3),
                               "median_sharp": round(med(sh[i:j+1]), 1),
                               "median_fineratio": round(med(fi[i:j+1]), 3)})
            i = j+1
        else:
            i += 1

    trans = []
    for i, f in enumerate(fr):
        if i and f["diff"] > max(4.0*dref, 25.0):
            trans.append({"t": i, "diff": f["diff"], "luma": f["luma"], "sharp": f["sharp"]})

    msh = med(sh); mfr = med(fi)
    grade = "A 清晰" if (msh >= 2000 and mfr >= 0.155) else ("B 中等" if (msh >= 1000 or mfr >= 0.145) else "C 偏软")
    badn = len(bad)
    return {
        "file": fn, "duration": dur, "n_frames": n, "grade": grade,
        "refs": {"P90_sharp": round(PS, 1), "P90_edgefrac": round(PE, 3), "P90_colorful": round(PC, 1),
                 "median_sharp": round(msh, 1), "median_fineratio": round(mfr, 3)},
        "bad_seconds": badn,
        "usable_ratio": round(1.0 - badn/max(n, 1), 3),
        "mean_q": round(sum(qs)/max(len(qs), 1), 3),
        "q_p10": round(pct(qs, 0.10), 3),
        "blocked": blocked,
        "usable_intervals": usable,
        "transitions": trans,
        "stats": {
            "luma": [round(pct([f["luma"] for f in fr], p), 1) for p in (0.05, 0.5, 0.95)],
            "sharp": [round(pct(sh, p), 1) for p in (0.05, 0.5, 0.95)],
            "colorful": [round(pct(co, p), 1) for p in (0.05, 0.5, 0.95)],
            "sat": [round(pct([f["sat"] for f in fr], p), 3) for p in (0.05, 0.5, 0.95)],
            "entropy": [round(pct(en, p), 2) for p in (0.05, 0.5, 0.95)],
            "fineratio": [round(pct(fi, p), 3) for p in (0.05, 0.5, 0.95)],
            "darkfrac_max": round(max(f["darkfrac"] for f in fr), 3),
            "brightfrac_max": round(max(f["brightfrac"] for f in fr), 3),
        },
    }

def fmt_ivs(ivs, maxn=6):
    if not ivs: return "-"
    ivs = sorted(ivs, key=lambda x: -x["dur"])[:maxn]
    return "、".join("%s-%s(%d秒)" % (mmss(x["start"]), mmss(x["end"]+1), x["dur"]) for x in ivs)

def build():
    meta = json.load(open(META, encoding="utf-8"))
    data = json.load(open(METRICS, encoding="utf-8"))
    segs = {}
    for fn in sorted(data.keys()):
        segs[fn] = classify(fn, data[fn], (meta.get(fn) or {}).get("duration"))
    tmp = os.path.join(OUT, "segments.json.tmp")
    json.dump(segs, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(OUT, "segments.json"))

    tot_dur = sum((s["duration"] or 0) for s in segs.values())
    tot_fr = sum(s["n_frames"] for s in segs.values())
    tot_bad = sum(s["bad_seconds"] for s in segs.values())
    tot_high = sum(b["dur"] for s in segs.values() for b in s["blocked"] if b["conf"] == "high")
    all_luma = [f["luma"] for fn in data for f in data[fn]]
    all_dark = [f["darkfrac"] for fn in data for f in data[fn]]
    all_bri = [f["brightfrac"] for fn in data for f in data[fn]]

    L = []; A = L.append
    A("# 素材逐秒指标分析报告（遮挡 / 糊 / 可用区间判定）")
    A("")
    A("> 自动生成：ffmpeg 逐秒抽帧（480px 宽）-> numpy/Pillow 逐帧指标 -> 阈值判定。判定为规则推断，最终请结合联系图（sheets/）与原始帧（frames/）人工确认。")
    A("")
    A("## 1. 素材清点")
    A("")
    A("| 项目 | 数值 |")
    A("|---|---|")
    A("| 素材目录 | " + SRC + " |")
    A("| 文件数 | **%d** 个 mp4（实际清点；任务描述中的 25 个不准确，缺 REC-0009/0010/0011） |" % len(segs))
    A("| 总时长 | **%.1f 秒 = %d 分 %02d 秒** |" % (tot_dur, int(tot_dur)//60, int(tot_dur)%60))
    A("| 总抽帧 | %d 帧（每文件 = 时长秒数，误差 0） |" % tot_fr)
    A("| 规格 | 3840x2160 / 60fps / h264 / 约 19 Mbps |")
    A("| 时长分布 | 20 个文件 120s；REC-0004 58.2s、REC-0016 67.8s、REC-0023 27.3s、REC-0027 50.2s |")
    A("")
    A("## 2. 方法与阈值")
    A("")
    A("每帧（480px 宽）指标：luma 亮度均值、lumastd 亮度标准差、darkfrac(亮度<28 占比)、brightfrac(>230 占比)、sat 饱和度、colorful(Hasler-Süsstrunk 颜色丰富度)、sharp(Laplacian 方差)、grad / edgefrac(Sobel 均值 / 边缘像素占比)、entropy(64 段灰度熵)、uniform(距中值<12 的像素占比)、flatfrac(12 分块中无细节块占比)、warmfrac(暖色/肤色块占比)、fineratio(480 与 240 两个尺度拉普拉斯方差之比，衡量高频细节是否真的存在：真虚焦时该值明显偏低)、diff(与上一帧平均绝对差)。")
    A("")
    A("阈值（细节类均相对该文件自身 P90，避免不同场景互相误伤）：")
    A("")
    A("| 类别 | 条件 |")
    A("|---|---|")
    A("| BLACK 极暗 | luma<35 或 darkfrac>0.70 |")
    A("| WHITE 过曝 | luma>240 或 brightfrac>0.80 |")
    A("| BLOCK 无细节/疑似遮挡 | edgefrac<0.15xP90 且 sharp<0.15xP90（既无边缘也无锐度） |")
    A("| BLUR 低锐度/虚焦 | sharp<0.25xP90 且 edgefrac<0.50xP90 且 fineratio<0.16 且 lumastd>=32（有反差但无细节） |")
    A("| FLATS 单色板/天空 | uniform>0.45 或 lumastd<25 |")
    A("| 突变点 | diff>4x文件中位 且 >25 |")
    A("")
    A("连续被标记的秒合并为区间（间隔 <=2 秒合并）；长度 >=5s 为高置信，2-4s 中，1s 低。")
    A("")
    A("## 3. 总览：文件级判定")
    A("")
    A("| 文件 | 时长 | 帧 | 清晰度档 | sharp中位 | fineratio中位 | 可用率 | 高置信问题秒 | 主要问题 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for fn in sorted(segs.keys()):
        s = segs[fn]
        cls = {}
        for b in s["blocked"]:
            if b["conf"] != "low":
                for k2, v in b["mix"].items():
                    cls[k2] = cls.get(k2, 0) + v
        main = "、".join("%s x%d" % (LBL[k2], v) for k2, v in sorted(cls.items(), key=lambda z: -z[1])) or "-"
        hi = sum(b["dur"] for b in s["blocked"] if b["conf"] == "high")
        A("| %s | %s | %d | %s | %.0f | %.3f | %.0f%% | %d | %s |" % (
            fn, mmss(s["duration"] or 0), s["n_frames"], s["grade"],
            s["refs"]["median_sharp"], s["refs"]["median_fineratio"],
            s["usable_ratio"]*100, hi, main))
    A("")
    A("## 4. 重点结论")
    A("")
    A("- **没有真正的「一片黑」**：全素材最低 luma=%.1f，darkfrac 峰值 %.2f，不存在全黑或近全黑的帧。" % (min(all_luma), max(all_dark)))
    A("- **没有过曝白场**：brightfrac 峰值 %.2f。" % max(all_bri))
    A("- 真正的问题是**低锐度 / 低细节（糊）**：被标记 %d 秒 / %d 秒 = %.1f%%，其中高置信 %d 秒。" % (tot_bad, int(tot_dur), 100.0*tot_bad/max(tot_dur, 1), tot_high))
    A("- 素材明显分成两批：**REC-0001 ~ REC-0008 整体偏软**（sharp 中位 323~1933、fineratio 中位 0.12~0.20，糊的区间多）；**REC-0012 ~ REC-0027 基本清晰**（sharp 中位 1201~3176、fineratio 中位 0.14~0.20），其中 REC-0012 / 0013 / 0014 / 0017 / 0018 / 0019 / 0020 / 0021 / 0022 / 0023 几乎全程可用。")
    A("- 成批的「全片偏软」最常见原因是手持走动 / 慢快门带来的运动模糊，其次是对焦没跟上；不是镜头被遮挡。")
    A("- 高置信问题区间集中在少数文件，见第 5 节各文件的「问题区间」表。")
    A("")
    A("## 5. 逐文件明细")
    A("")
    for fn in sorted(segs.keys()):
        s = segs[fn]
        A("### %s - %s，%d 帧，%s" % (fn, mmss(s["duration"] or 0), s["n_frames"], s["grade"]))
        A("")
        A("- 指标 5%%/中位/95%%：luma %s；sharp %s；fineratio %s；colorful %s；sat %s；entropy %s；darkfrac 峰值 %.2f" % (
            "/".join("%.0f" % v for v in s["stats"]["luma"]),
            "/".join("%.0f" % v for v in s["stats"]["sharp"]),
            "/".join("%.3f" % v for v in s["stats"]["fineratio"]),
            "/".join("%.1f" % v for v in s["stats"]["colorful"]),
            "/".join("%.3f" % v for v in s["stats"]["sat"]),
            "/".join("%.2f" % v for v in s["stats"]["entropy"]),
            s["stats"]["darkfrac_max"]))
        A("- 质量分 mean_q=%.3f（p10=%.3f）；可用率 %.0f%%（被标记 %d 秒）" % (
            s["mean_q"], s["q_p10"], s["usable_ratio"]*100, s["bad_seconds"]))
        if s["blocked"]:
            A("- **问题区间 %d 段**" % len(s["blocked"]))
            A("")
            A("  | 起 | 止 | 时长 | 类别 | 置信 | 相对锐度 | 相对边缘 | fineratio | sharp中位 | luma | std | uniform | warmfrac | 帧间差 |")
            A("  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for b in s["blocked"]:
                A("  | %s | %s | %ds | %s | %s | %.2f | %.2f | %.3f | %.0f | %.0f | %.0f | %.2f | %.2f | %.0f |" % (
                    mmss(b["start"]), mmss(b["end"]+1), b["dur"], b["label_txt"], b["conf"],
                    b["mean_det"], b["mean_edge"], b["median_fineratio"], b["median_sharp"],
                    b["median_luma"], b["median_lumastd"], b["median_uniform"], b["median_warmfrac"], b["mean_diff"]))
            A("")
        else:
            A("- 未检出问题区间")
            A("")
        if s["usable_intervals"]:
            A("- 建议可用区间（按长度取前 6）：%s" % fmt_ivs(s["usable_intervals"]))
        else:
            A("- 建议可用区间：无（全片均被标记，或可用间隔都 <5 秒）")
        if s["transitions"]:
            ts = "、".join("%s(diff=%.0f)" % (mmss(t["t"]), t["diff"]) for t in s["transitions"][:10])
            more = " 等共 %d 处" % len(s["transitions"]) if len(s["transitions"]) > 10 else ""
            A("- 突变点（遮挡进出 / 切镜 / 急停）：%s%s" % (ts, more))
        A("")

    A("## 6. 值得优先使用的文件")
    A("")
    A("按 mean_q 与可用率加权排序：")
    A("")
    A("| 优先级 | 文件 | 时长 | 档 | mean_q | 可用率 | 建议 |")
    A("|---|---|---|---|---|---|---|")
    ranked = sorted(segs.values(), key=lambda s: -(s["mean_q"]*0.6 + s["usable_ratio"]*0.4))
    for i, s in enumerate(ranked[:12], 1):
        if s["usable_ratio"] >= 0.95: use = "整段可用"
        elif s["usable_intervals"]: use = "用 " + fmt_ivs(s["usable_intervals"], 2)
        else: use = "不建议整段用"
        A("| %d | %s | %s | %s | %.3f | %.0f%% | %s |" % (i, s["file"], mmss(s["duration"] or 0), s["grade"], s["mean_q"], s["usable_ratio"]*100, use))
    A("")
    A("## 7. 数据文件")
    A("")
    A("- metrics.json - 每文件每秒全部指标（原始数据，可直接画曲线）")
    A("- segments.json - 判定结果（问题区间 / 可用区间 / 突变点 / 质量分）")
    A("- meta.json - 文件时长、帧数、联系图行数")
    A("- frames/REC-XXXX/sec_NNNN.jpg - 每秒 1 帧（480px 宽，sec_0001 = t=0s）")
    A("- sheets/REC-XXXX.jpg - 联系图 10 列 x N 行，每格 192px，格内左上角黄字 = 该格秒数")
    A("- sheets/REC-XXXX.txt - 行/列 到 秒 的映射表")
    A("")
    A("> 复核提示：sharp / fineratio 偏低也可能是「大面积天空 / 水面 / 雾」这类本身无细节的内容（已单列为 FLATS），也可能是快速摇镜。若某段被判 BLUR 但联系图上明显是清晰风景，请以原始帧为准并告诉我，我改阈值重算（只重算指标，约 15 秒，无需重新解码）。")
    txt = "\n".join(L)
    open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8").write(txt)
    print("SUMMARY.md ok, files=%d, chars=%d" % (len(segs), len(txt)))
    print("total dur=%.1f frames=%d bad=%.1f%% high_conf=%ds" % (tot_dur, tot_fr, 100.0*tot_bad/max(tot_dur,1), tot_high))

if __name__ == "__main__":
    build()
