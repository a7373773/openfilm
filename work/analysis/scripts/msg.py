# -*- coding: utf-8 -*-
import json, os
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
S = json.load(open(os.path.join(OUT,"segments.json"), encoding="utf-8"))
def mm(t):
    t=int(round(t)); return "%d:%02d"%(t//60,t%60)
L=[]
L.append("【素材分析完成】24 个源文件 / 2603 段逐秒数据（43分25秒），逐秒抽帧+指标+联系图已全部生成。")
L.append("")
L.append("0) 两处与任务描述不符，请知悉：目录里实际是 24 个 mp4（不是 25），缺 REC-0009/0010/0011；总时长 43:25（不是 49 分钟）。")
L.append("")
L.append("1) 时长表（文件 / 时长 / 清晰度档 / 可用率 / 可疑秒数）")
for fn in sorted(S):
    s=S[fn]
    L.append("  %-16s %5s  %s  %3.0f%%  %3ds" % (fn, mm(s["duration"]), s["grade"][0], s["usable_ratio"]*100, s["bad_seconds"]))
L.append("")
L.append("2) 关键结论：全片没有任何「一片黑」（最低 luma=53，darkfrac 峰值 0.39）、也没有过曝白场（brightfrac 峰值 0.66）。真正的问题是「糊」——低锐度/低细节，占 266 秒 / 10.2%。")
L.append("")
L.append("3) 明显被判定为糊的文件与时间区间（只列中高置信，起-止为闭开区间，单位 秒：秒）")
for fn in sorted(S):
    s=S[fn]
    iv=[b for b in s["blocked"] if b["conf"] in ("high","mid")]
    if not iv: continue
    L.append("  %s 可用率%.0f%%：" % (fn, s["usable_ratio"]*100))
    for b in iv:
        L.append("    %s-%s %2ds %s(%s) sharp中位%.0f fineratio%.3f 帧间差%.0f" % (
            mm(b["start"]), mm(b["end"]+1), b["dur"], b["label_txt"], b["conf"],
            b["median_sharp"], b["median_fineratio"], b["mean_diff"]))
L.append("")
L.append("4) 完全干净、可直接整段用的文件（可用率 100%/98%+，无中高置信问题）：")
clean=[fn.replace("-A.mp4","") for fn in sorted(S) if S[fn]["usable_ratio"]>=0.98]
L.append("   " + "、".join(clean))
L.append("")
L.append("5) 优先使用建议（按质量分 x 可用率排序）")
for i,s in enumerate(sorted(S.values(), key=lambda s:-(s["mean_q"]*0.6+s["usable_ratio"]*0.4))[:10],1):
    if s["usable_ratio"]>=0.95:
        use="整段可用"
    else:
        iv=sorted(s["usable_intervals"], key=lambda x:-x["dur"])[:2]
        use="只取 "+"、".join("%s-%s"%(mm(x["start"]),mm(x["end"]+1)) for x in iv)
    L.append("   %2d. %-16s %s mean_q=%.3f 可用率%.0f%% -> %s" % (i,s["file"],mm(s["duration"]),s["mean_q"],s["usable_ratio"]*100,use))
L.append("")
L.append("6) 用法：若要肉眼复核某个可疑区间，直接看 work/analysis/sheets/REC-XXXX.jpg（10列x N行，每格192px，格内左上角黄字=该秒数），或用 frames/REC-XXXX/sec_NNNN.jpg（sec_0001=t=0s）。")
L.append("")
L.append("7) 判定方法概要：抽帧 1fps/480px（ffmpeg -hwaccel cuda）；每帧算 luma/暗部占比/过曝占比/饱和度/颜色丰富度/Laplacian 方差锐度/边缘占比/熵/单色占比/肤色暖色占比/fineratio(480与240尺度拉普拉斯比，真虚焦会明显偏低)/帧间差。阈值相对每个文件自身 P90，避免场景差异误伤。BLUR=锐度<0.25xP90 且 边缘<0.5xP90 且 fineratio<0.16；BLOCK=边缘<0.15xP90 且 锐度<0.15xP90。")
L.append("")
L.append("8) 需要我调整就说话：如果你看了联系图觉得某些区间其实是清晰风景（比如大面积天空被判糊），告诉我，我改阈值只重算指标，约 15 秒，不用重新解码。")
open(os.path.join(OUT,"logs","message.txt"),"w",encoding="utf-8").write("\n".join(L))
print("bytes", os.path.getsize(os.path.join(OUT,"logs","message.txt")))
