
import json, os
W = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work"
def fmt(x):
    return "%d:%04.1f" % (int(x // 60), x - 60 * int(x // 60))
edl = json.load(open(os.path.join(W, "lead", "edl.json"), encoding="utf-8-sig"))
shots = edl["shots"]
t = 0.0; rows = []
for i, s in enumerate(shots):
    d = s["dur"]; xf = s.get("xfade", 0.0); src_len = d * s["speed"]
    rows.append((i + 1, t, t + d, s["file"], s["start"], s["start"] + src_len, s["speed"], s.get("scene"), s.get("p_landscape")))
    t = t + d - xf
total = t
out = ["# 镜头表 · 风景混剪 v1", "",
       "成片总长 **%.1f 秒** ｜ 1920x1080 / 30fps / H.264 High / AAC 48kHz ｜ 18 个镜头 / %d 个源文件" % (total, len(set(r[3] for r in rows))), "",
       "| # | 成片时间 | 源文件 | 源时间码 | 速度 | CLIP判定 | CLIP风景置信 |",
       "|---|---|---|---|---|---|---|"]
for (n, a, b, f, s0, s1, spd, sc, pl) in rows:
    sp = "1.0x" if abs(spd - 1.0) < 1e-6 else ("0.5x 慢动作" if abs(spd - 0.5) < 1e-6 else "%.2fx" % spd)
    out.append("| %d | %s–%s | %s | %s–%s | %s | %s | %s |" % (
        n, fmt(a), fmt(b), f, fmt(s0), fmt(s1), sp, sc or "-", pl if pl is not None else "-"))
open(os.path.join(W, "lead", "shotlist.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print("TOTAL %.3f written" % total)
print("\n".join(out[6:12]))
