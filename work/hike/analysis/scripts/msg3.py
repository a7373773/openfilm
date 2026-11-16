# -*- coding: utf-8 -*-
import os, json
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
pc = json.load(open(os.path.join(OUT,"per_clip.json"),encoding="utf-8"))
mask = json.load(open(os.path.join(OUT,"mask.json"),encoding="utf-8"))
dp = json.load(open(os.path.join(OUT,"dupes.json"),encoding="utf-8"))
meta = json.load(open(os.path.join(OUT,"meta.json"),encoding="utf-8"))
order = sorted(pc.keys())
tot = sum(meta[f]["n_frames"]*0.5 for f in order)
keep = sum(pc[f]["keep_secs"] for f in order)
nkeep = sum(1 for f in order if pc[f]["keep"])
L=[];A=L.append
A("【爬山素材 task-4 完成】74 镜头 / 496.5 秒全部抽帧+指标+判重+保留区间规划已交付（work/hike/analysis/）")
A("")
A("一、重复镜头：真正需要去重的只有 1 组")
A("  ✔ C1827(2.0s) 与 C1828(4.0s) 是同一静止画面的两次拍摄 → 弃用 C1827，用 C1828")
A("    证据：C1827 的 4 帧全部命中 C1828 对应帧，dHash 距离 4~5/64、HSV 直方图余弦 0.94，两段内部帧差≈0（都是定格式静止机位），C1828 更长。")
A("  ✘ C1897 / C1898（你怀疑的那对）：**不是重复**，时长同为 17.02s 是巧合。")
A("    证据：帧级完全对不上（中位 dHash 26/64，没有任何一对帧满足 dHash<=10 且直方图余弦>=0.93，最佳像素相关只有 0.76）；两段运动特征相反——C1897 是快摇（帧间 dHash 变化 19~35），C1898 是稳住慢摇（0~9）。属同一片开阔风景的两个不同镜头，都能用；若怕观感重复，留 C1898 即可（更清晰，sharp 1139 vs 389）。")
A("  ✘ C1843 / C1844：**不是重复**。中位 dHash 33/64、直方图余弦 0.78、像素相关 0.29；C1843 平均亮度 47（暗林），C1844 144（明亮），完全不同的画面。")
A("  ⚠ C1905 / C1906：互相极像（余弦 0.993、像素相关 0.93），但两段都是「无细节画面」——不是有效镜头，已整段剔除，去重无意义。")
A("  方法说明：先算整段颜色直方图会误报（本批 26 对镜头色分布余弦 >=0.96，全是同一片林子），所以判据用「帧级 1:1 对应」（dHash<=10 且直方图余弦>=0.93）。")
A("")
A("二、每镜头建议保留区间（格式 镜头[起-止]质量档，档 A=清晰 B=一般 C=偏暗偏软；未列出=整段弃用）")
secs="起步 林间 爬升 开阔 登顶".split()
for s in secs:
    items=[f for f in order if pc[f]["section"]==s]
    if not items: continue
    A("  【%s】" % s)
    line="   "
    for f in items:
        r=pc[f]
        nm=f.replace("S03.mp4","")
        if r["keep"]:
            line += "%s[%.1f-%.1f]%s  " % (nm, r["keep"][0][0], r["keep"][0][1], r["grade"])
        else:
            line += "%s[弃用]  " % nm
        if len(line)>92:
            A(line); line="   "
    if line.strip(): A(line)
A("")
A("  合计：%d 个镜头参与，保留 %.1f 秒（目标 180 秒，留 14%% 余量给转场/节奏修剪）" % (nkeep, keep))
A("")
A("三、开场 / 登顶推荐")
A("  开场（前 14 个镜头里亮度 100~190、最清晰的）：")
A("   1) C1834 取 0.0-3.5s（sharp 2966、亮度 145、绿色占比 0.59）——起步林道，画面最干净，适合作第一镜")
A("   2) C1825 取 0.5-4.0s（sharp 2360、亮度 132、绿色 0.40）")
A("   3) C1828 取 0.5-4.0s（sharp 1818、亮度 136、绿色 0.28）")
A("  登顶（末段可用镜头，C1905~C1909 全废，只剩 C1892~C1899）：")
A("   1) C1898 取 0.5-4.5s（亮度 165、天空占比 0.23、sharp 1139）——最亮最开阔，收尾首选")
A("   2) C1899 取 0.5-4.0s（亮度 137、sharp 1058、绿色 0.80 偏高）")
A("   3) C1896 取 2.0-5.5s（亮度 167、sharp 962）")
A("   另：C1894(亮度 216)、C1893(193)、C1892(188) 是最「敞亮」的，但 sharp 只有 536~698，偏软，适合当空镜/光晕过渡。")
A("")
A("四、其它要点")
A("  - 5 个镜头整段不可用：C1905(13.0s) C1906(4.0s) C1907(9.5s) C1908(7.0s) C1909(5.5s)，edgefrac 只有 0.05~0.13、sharp 15~191，典型的镜头被手/衣物挡住或装包过程。")
A("  - 判为遮挡/糊共 55.5 秒（11.2%），除上面 5 个整段外，还有 C1883 3.0-12.0s、C1897 11.5-17.0s 两段局部。")
A("  - 前段到中段（C1836~C1868 一带）普遍偏暗：20 个镜头平均亮度 <80（最暗 C1848=25、C1840=42、C1849=43），是清晨林间，不是遮挡。我在 per_clip.json 里给了每个镜头的平均亮度，剪辑记得调色/提亮。")
A("  - 质量分档：A 档 25 个镜头（清晰，可直接用）、B 档 24 个（一般）、C 档 19 个（偏暗/偏软，建议只当 1~2 秒过渡）：")
A("      C 档 = C1824 C1829 C1836 C1839 C1840 C1842 C1843 C1845 C1847 C1865 C1867 C1868 C1881 C1883 C1887 C1892 C1893 C1894 C1897")
A("  - 帧率差异：C1824S03 是 59.94fps，其余 73 个都是 29.97fps，剪辑时间线注意统一（或者直接按秒切）。")
A("")
A("五、文件清单（work/hike/analysis/）")
A("  frames/ 74 个目录 993 张（2fps/480px）｜metrics.json 74 文件逐帧指标｜mask.json 遮挡/糊区间｜dupes.json 判重（4 条：1 真重复 + 1 双废 + 2 核验非重复）｜per_clip.json 每镜头时长/可用率/构图/保留区间/质量档｜SUMMARY.md 总表+章节+推荐")
open(os.path.join(OUT,"logs","message3.txt"),"w",encoding="utf-8").write("\n".join(L))
print("bytes", os.path.getsize(os.path.join(OUT,"logs","message3.txt")))
