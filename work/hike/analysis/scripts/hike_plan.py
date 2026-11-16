# -*- coding: utf-8 -*-
"""per_clip.json + SUMMARY.md: 保留区间规划（按镜头顺序，去遮挡/去重复，总时长 >=180s）。"""
import os, json, math
import numpy as np
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
M = json.load(open(os.path.join(OUT, "metrics.json"), encoding="utf-8"))
meta = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8"))
det = json.load(open(os.path.join(OUT, "mask_detail.json"), encoding="utf-8"))
mask = json.load(open(os.path.join(OUT, "mask.json"), encoding="utf-8"))
H = os.path.join(OUT, "hashes")
BLOCKLBL = ("BLACK", "WHITE", "BLOCK", "BLUR")
SECTIONS = [(0.00, 0.20, "起步"), (0.20, 0.42, "林间"), (0.42, 0.66, "爬升"),
            (0.66, 0.86, "开阔"), (0.86, 1.01, "登顶")]
DUP_SKIP = {"C1827S03.mp4": "C1828S03.mp4"}   # C1827 是 C1828 的短版重复

def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)

def load_hashes(fn):
    return json.load(open(os.path.join(H, fn.replace(".mp4", "") + ".json"), encoding="utf-8"))

def usable_flags(fn):
    n = len(M[fn]); bad = set()
    for r in det[fn]["runs_all"]:
        if r["label"] in BLOCKLBL:
            a = int(round(r["start"] * 2)); b = int(round(r["end"] * 2))
            for t in range(max(0, a), min(n, b)): bad.add(t)
    return [i not in bad for i in range(n)]

def sample_q(f):
    s = clamp(f["sharp"] / 1600.0)
    fi = clamp(f["fineratio"] / 0.20)
    e = clamp(f["edgefrac"] / 0.75)
    b = 1.0 - min(1.0, abs(f["luma"] - 135.0) / 120.0)
    mo = clamp(1.0 - abs(f["diff"] - 14.0) / 30.0)
    return 0.35*s + 0.25*fi + 0.15*e + 0.15*b + 0.10*mo

def best_window(fr, flags, want_len, min_len=2.0, max_len=8.0):
    n = len(fr)
    want = max(min_len, min(max_len, want_len))
    best = None
    Lmax = int(round(min(want, n*0.5) * 2))
    for L in range(int(round(min_len*2)), Lmax + 1):
        for st in range(0, n - L + 1):
            if not all(flags[st:st+L]):
                continue
            qs = [sample_q(fr[i]) for i in range(st, st+L)]
            mq = sum(qs) / L
            dur = L * 0.5
            # 长度偏好：2.5~5s 最好；过短信息量少，过长剪辑节奏慢
            len_bonus = 1.0 + 0.05 * min(dur, 4.0) - 0.02 * max(0.0, dur - 5.0)
            score = mq * len_bonus
            if best is None or score > best[0]:
                best = (score, st, L, mq)
    if best is None:
        return None
    score, st, L, mq = best
    return {"start": round(st*0.5, 2), "end": round((st+L)*0.5, 2), "samples": L, "q": round(mq, 3),
            "score": round(score, 4)}

def main():
    files = sorted(M.keys())
    tot = sum(meta[fn]["n_frames"]*0.5 for fn in files)
    # 章节按"可用素材"的时间推进来分，避免末尾不可用镜头吃掉登顶段落
    use = {fn: sum(usable_flags(fn))*0.5 for fn in files}
    utot = max(sum(use.values()), 1e-6)
    cum = 0.0; sect = {}
    for fn in files:
        d = use[fn]
        mid = (cum + d*0.5) / utot
        for a, b, nm in SECTIONS:
            if a <= mid < b:
                sect[fn] = nm; break
        cum += d
    recs = {}
    for fn in files:
        fr = M[fn]; n = len(fr); dur = n*0.5
        h = load_hashes(fn)
        flags = usable_flags(fn)
        usable = sum(flags)*0.5
        rec = {"file": fn, "dur": round(dur, 2), "section": sect[fn],
               "usable_secs": round(usable, 2), "usable_ratio": round(usable/max(dur, 0.1), 3),
               "mean_sharp": round(float(np.mean([f["sharp"] for f in fr])), 1),
               "mean_fineratio": round(float(np.mean([f["fineratio"] for f in fr])), 3),
               "mean_luma": round(float(np.mean([f["luma"] for f in fr])), 1),
               "motion": round(float(np.mean([f["diff"] for f in fr])), 1),
               "first": {"sky": h["frames"][0]["sky"], "green": h["frames"][0]["green"]},
               "mid": {"sky": h["frames"][n//2]["sky"], "green": h["frames"][n//2]["green"]},
               "mask_runs": mask[fn]["runs"], "keep": [], "keep_secs": 0.0, "note": ""}
        if fn in DUP_SKIP:
            rec["note"] = "重复镜头，与 %s 同画面，建议用后者" % DUP_SKIP[fn]
            rec["dup_of"] = DUP_SKIP[fn]
        elif usable < 2.0:
            rec["note"] = "可用不足 2 秒（遮挡/糊），不入选"
        else:
            want = 2.0 if usable < 3.5 else (3.5 if usable < 9 else (4.5 if usable < 14 else 5.5))
            w = best_window(fr, flags, want, min_len=2.0, max_len=min(10.0, usable))
            if w:
                rec["keep"] = [[w["start"], w["end"]]]
                rec["keep_secs"] = round(w["end"] - w["start"], 2)
                rec["q"] = w["q"]
        recs[fn] = rec
    # ---- 总量调整到 190~215 秒 ----
    def total_keep():
        return sum(r["keep_secs"] for r in recs.values())
    def eligible():
        return [r for r in recs.values() if r["keep"] and r["file"] not in DUP_SKIP]
    rounds = 0
    while total_keep() < 190.0 and rounds < 40:
        cands = sorted(eligible(), key=lambda r: r.get("q", 0), reverse=True)
        changed = False
        for r in cands:
            fr = M[r["file"]]; flags = usable_flags(r["file"]); n = len(fr)
            cur = r["keep"][0][1] - r["keep"][0][0]
            if cur + 0.5 <= min(10.0, r["usable_secs"]) and cur + 0.5 <= n*0.5:
                w = best_window(fr, flags, cur + 0.5, min_len=2.0, max_len=min(10.0, r["usable_secs"]))
                if w and (w["end"] - w["start"]) > cur:
                    r["keep"] = [[w["start"], w["end"]]]; r["keep_secs"] = round(w["end"]-w["start"], 2)
                    r["q"] = w["q"]; changed = True
                    break
        rounds += 1
        if not changed:
            break
    while total_keep() > 205.0 and rounds < 80:
        cands = sorted(eligible(), key=lambda r: r.get("q", 0))
        changed = False
        for r in cands:
            cur = r["keep"][0][1] - r["keep"][0][0]
            if cur - 0.5 >= 2.0:
                fr = M[r["file"]]; flags = usable_flags(r["file"])
                w = best_window(fr, flags, cur - 0.5, min_len=2.0, max_len=min(10.0, r["usable_secs"]))
                if w and (w["end"]-w["start"]) < cur:
                    r["keep"] = [[w["start"], w["end"]]]; r["keep_secs"] = round(w["end"]-w["start"], 2)
                    r["q"] = w["q"]; changed = True
                    break
        rounds += 1
        if not changed:
            break
    # quality grade
    for r in recs.values():
        s = r["mean_sharp"]; f = r["mean_fineratio"]; l = r["mean_luma"]
        if not r["keep"]:
            r["grade"] = "-"
        elif s >= 1500 and f >= 0.13:
            r["grade"] = "A"
        elif s >= 700 and f >= 0.10:
            r["grade"] = "B"
        else:
            r["grade"] = "C"
    keep_total = round(total_keep(), 2)
    n_keep = sum(1 for r in recs.values() if r["keep"])
    json.dump(recs, open(os.path.join(OUT, "per_clip.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("clips kept: %d / %d   keep_total = %.2f s" % (n_keep, len(recs), keep_total))
    sec = {}
    for r in recs.values():
        if r["keep"]:
            sec[r["section"]] = sec.get(r["section"], 0) + r["keep_secs"]
    print("by section:", {k: round(v,1) for k, v in sec.items()})
    return recs, keep_total, n_keep, tot

def mmss(t):
    t = float(t); return "%d:%04.1f" % (int(t)//60, t - 60*(int(t)//60))

def write_dupes(recs):
    pairs = [
        ["C1827S03.mp4", [0.0, 2.0], "C1828S03.mp4", [0.0, 4.0], 1.0,
         "帧级重复：C1827 的 4 帧全部能在 C1828 中找到对应帧（dHash 距离 4~5/64、HSV 直方图余弦 0.94），两段都是静止机位同画面，C1828 更长（4.0s vs 2.0s）。建议只保留 C1828，C1827 弃用。"],
        ["C1905S03.mp4", [0.0, 13.0], "C1906S03.mp4", [0.0, 4.0], 0.99,
         "两段互相高度相似（直方图余弦 0.993、最佳帧 dHash 2/64、像素相关 0.93），但两段都是『无细节画面』（edgefrac 0.13、sharp 191/103，几乎没有可辨识结构），应全部弃用；不构成有效重复镜头。"],
        ["C1897S03.mp4", [0.0, 17.0], "C1898S03.mp4", [0.0, 17.0], 0.35,
         "经核验不是重复：两段时长同为 17.02s 属巧合。帧级对应不成立（中位 dHash 距离 26/64、无任何帧对满足 dHash<=10 且直方图余弦>=0.93、最佳像素相关仅 0.76）；运动特征相反——C1897 是快速摇镜（帧间 dHash 变化 19~35），C1898 是稳住慢摇（0~9）。结论：同一片开阔风景的两个不同镜头，可以都留；若想避免观感重复可只留 C1898。"],
        ["C1843S03.mp4", [0.0, 11.0], "C1844S03.mp4", [0.0, 4.5], 0.29,
         "经核验不是重复：中位 dHash 距离 33/64、直方图余弦 0.78、最佳帧像素相关 0.29；C1843 平均亮度 47（暗光林间），C1844 平均 144（明亮），构图与曝光都不同。"],
    ]
    json.dump(pairs, open(os.path.join(OUT, "dupes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return pairs

def write_summary(recs, keep_total, n_keep, tot, pairs):
    L = []; A = L.append
    A("# 爬山素材分析报告（immich-20261112_115253）")
    A("")
    A("> 自动生成：ffmpeg 2fps 抽帧（480px）-> 逐帧指标 -> 阈值判定 -> 保留区间规划。判定为规则推断，建议结合 frames/ 复核。")
    A("")
    A("## 1. 素材总览")
    A("")
    A("| 项目 | 数值 |")
    A("|---|---|")
    A("| 目录 | 素材/immich-20261112_115253 |")
    A("| 文件数 | **74** 个 mp4（镜头号 C1824 -> C1909，中间有跳号） |")
    A("| 总时长 | **%.2f 秒 = %d 分 %02d 秒** |" % (tot, int(tot)//60, int(tot)%60))
    A("| 规格 | 1920x1080，73 个 29.97fps + C1824S03 为 59.94fps；每条都有音轨 |")
    A("| 抽帧 | 2fps（每 0.5 秒 1 帧），宽 480，共 %d 帧 |" % sum(meta[fn]["n_frames"] for fn in recs))
    A("| 判为遮挡/糊 | %.1f 秒（占 %.1f%%），其中 5 个镜头整段不可用（C1905~C1909） |" % (
        sum(r["dur"]-r["usable_secs"] for r in recs.values()), 100.0*sum(r["dur"]-r["usable_secs"] for r in recs.values())/tot))
    A("| 建议保留 | **%.1f 秒**，来自 **%d** 个镜头（成片 3:00 = 180s，留了约 %.0f%% 余量） |" % (keep_total, n_keep, 100.0*(keep_total-180)/180))
    A("| 重复镜头 | 1 组（C1827 是 C1828 的短版）；另有 2 组经核验「不是重复」 |")
    A("")
    A("## 2. 重复镜头判定（dupes.json）")
    A("")
    A("方法：每 0.5 秒帧算 dHash(64bit) + aHash + HSV 直方图(H12+S4+V8)，跨文件比对；判据为「帧级对应」——A 的每一帧能否在 B 中找到 dHash<=10 且直方图余弦>=0.93 的帧、且对应关系单调。**只看颜色直方图会误报**：本批素材里 26 对镜头的整段色分布余弦 >=0.96（都是同一片林子），逐帧对应才能区分。")
    A("")
    VERD = {("C1827S03.mp4","C1828S03.mp4"): "帧级重复 -> 弃用 C1827，用 C1828",
            ("C1905S03.mp4","C1906S03.mp4"): "两段都是无细节画面 -> 全部弃用（去重无意义）",
            ("C1897S03.mp4","C1898S03.mp4"): "不是重复 -> 两段可都留（建议只留 C1898）",
            ("C1843S03.mp4","C1844S03.mp4"): "不是重复 -> 两段都可留"}
    A("| A | B | 相似度 | 结论 |")
    A("|---|---|---|---|")
    for p in pairs:
        A("| %s | %s | %.2f | %s |" % (p[0], p[2], p[4], VERD.get((p[0], p[2]), "见 dupes.json")))
    A("")
    A("详细理由见 dupes.json 的第 6 项文字说明。**结论：真正需要去重的只有 C1827（用 C1828 代替）。**")
    A("")
    A("## 3. 章节划分（按拍摄顺序）")
    A("")
    A("| 章节 | 镜头范围 | 保留时长 |")
    A("|---|---|---|")
    order = sorted(recs.keys())
    secs = {}
    for fn in order:
        r = recs[fn]
        if r["keep"]:
            secs.setdefault(r["section"], [fn, fn, 0.0])
            secs[r["section"]][1] = fn
            secs[r["section"]][2] += r["keep_secs"]
    for a, b, nm in SECTIONS:
        if nm in secs:
            f0, f1, s = secs[nm]
            A("| %s | %s ~ %s | %.1fs |" % (nm, f0.replace("S03.mp4",""), f1.replace("S03.mp4",""), s))
    A("")
    A("## 4. 逐镜头表")
    A("")
    A("| # | 镜头 | 时长 | 章节 | 档 | 可用率 | sharp | fineratio | 平均亮度 | 运动量 | 天空/绿色 | 建议保留 | 备注 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, fn in enumerate(order, 1):
        r = recs[fn]
        keep = "、".join("%.1f-%.1f" % (a, b) for a, b in r["keep"]) if r["keep"] else "-"
        note = r["note"]
        if not note and r["grade"] == "C":
            note = "偏暗/偏软，仅可做过渡"
        A("| %d | %s | %.1f | %s | %s | %.0f%% | %.0f | %.3f | %.0f | %.1f | %.2f/%.2f | %s | %s |" % (
            i, fn.replace("S03.mp4", ""), r["dur"], r["section"], r["grade"], r["usable_ratio"]*100,
            r["mean_sharp"], r["mean_fineratio"], r["mean_luma"], r["motion"],
            r["mid"]["sky"], r["mid"]["green"], keep, note))
    A("")
    A("## 5. 可用性判定标准（mask.json）")
    A("")
    A("2fps 采样，每 0.5 秒一帧；绝对阈值 + 相对本镜头 P90 结合：")
    A("")
    A("| 类别 | 条件 |")
    A("|---|---|")
    A("| BLACK 极暗/遮挡 | luma<35 且 edgefrac<0.45，或 相对锐度<0.12 且 edgefrac<0.18 |")
    A("| WHITE 过曝 | luma>235 或 brightfrac>0.80 |")
    A("| BLOCK 无细节/疑似遮挡 | edgefrac<0.20 且 sharp<350 |")
    A("| BLUR 低锐度/糊 | sharp<0.30xP90 且 fineratio<0.105 且 edgefrac<0.55xP90 |")
    A("| FLATS 天空/平板 | uniform>0.55 且 edgefrac<0.45xP90（**不进 mask**，天空镜头可用） |")
    A("")
    A("严重度：>=2s 记 high，1.0~1.5s 记 mid，0.5s 的抖动不进 mask。")
    A("")
    A("## 6. 完全不可用的镜头（整段遮挡/无细节）")
    A("")
    bad = [fn for fn in order if not recs[fn]["keep"]]
    for fn in bad:
        A("- %s（%.1fs）：%s" % (fn, recs[fn]["dur"], recs[fn]["note"] or "可用不足"))
    A("")
    A("## 7. 数据文件")
    A("")
    A("- metrics.json — 74 文件逐帧指标（2fps）")
    A("- mask.json — 遮挡/糊区间 [[起,止,严重度,sharp中位,fineratio],...]")
    A("- per_clip.json — 每镜头时长/可用率/构图/建议保留区间/质量档")
    A("- dupes.json — 重复镜头判定")
    A("- frames/CLIP/sec_NNNN.jpg — 2fps 抽帧（sec_0001 = t=0）")
    A("")
    A("## 8. 开场 / 登顶镜头建议")
    A("")
    order2 = sorted(recs.keys())
    cand = [recs[fn] for fn in order2 if recs[fn]["keep"]]
    op = sorted([r for r in cand if order2.index(r["file"]) < 14 and 100 <= r["mean_luma"] <= 190],
                key=lambda r: -(r.get("q", 0)))[:3]
    su = sorted([r for r in cand if r["section"] == "登顶" and r["mean_sharp"] >= 600], key=lambda r: -(r.get("q", 0)))[:3]
    if len(su) < 3:
        su += [r for r in sorted([r for r in cand if r["section"] == "登顶"], key=lambda r: -r["mean_luma"]) if r not in su][:3-len(su)]
    A("- **开场候选**（取前 14 个镜头里亮度 100~190 的最佳画面）：")
    for r in op:
        A("  - %s：保留 %.1f-%.1fs，sharp %.0f、均值亮度 %.0f、绿色占比 %.2f" % (
            r["file"].replace("S03.mp4",""), r["keep"][0][0], r["keep"][0][1], r["mean_sharp"], r["mean_luma"], r["mid"]["green"]))
    A("- **登顶候选**（末段可用镜头）：")
    for r in su:
        A("  - %s：保留 %.1f-%.1fs，均值亮度 %.0f、天空占比 %.2f、sharp %.0f" % (
            r["file"].replace("S03.mp4",""), r["keep"][0][0], r["keep"][0][1], r["mean_luma"], r["mid"]["sky"], r["mean_sharp"]))
    A("")
    A("> 注意：C1905~C1909 这 5 个序列号（拍摄时间在最后）整段是遮挡/无细节画面（像镜头被手或衣物挡住、或装包过程），")
    A("> 已全部剔除；登顶段落只能用 C1892~C1899 这批高亮度镜头来收尾。")
    txt = "\n".join(L)
    open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8").write(txt)
    print("SUMMARY chars:", len(txt))

if __name__ == "__main__":
    recs, keep_total, n_keep, tot = main()
    pairs = write_dupes(recs)
    write_summary(recs, keep_total, n_keep, tot, pairs)
    # 开场/登顶推荐
    order = sorted(recs.keys())
    cand = [recs[fn] for fn in order if recs[fn]["keep"]]
    opening = sorted([r for r in cand if order.index(r["file"]) < 14], key=lambda r: -(r.get("q",0)))[:3]
    summit = sorted([r for r in cand if r["section"] == "登顶"], key=lambda r: -(r.get("q",0)))[:3]
    print("OPENING:", [(r["file"], r["keep"], r.get("q"), r["mean_sharp"], r["mean_luma"]) for r in opening])
    print("SUMMIT:", [(r["file"], r["keep"], r.get("q"), r["mean_sharp"], r["mean_luma"]) for r in summit])
