# -*- coding: utf-8 -*-
"""Hike montage renderer: ordered shots, mixed hard-cuts + tasteful transitions,
title/lower-third/sticker overlays, progress bar, BGM."""
import json, os, subprocess, sys

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
SRC = os.path.join(ROOT, "素材", "immich-20261112_115253")
WK = os.path.join(ROOT, "work", "hike")
CLIPS = os.path.join(WK, "clips")
GFX = os.path.join(WK, "graphics")
OUT_W, OUT_H, FPS = 1920, 1080, 30

LOOK = ("curves=all='0/0.008 0.25/0.252 0.5/0.520 0.80/0.812 1/0.930',"
        "eq=saturation=1.04:contrast=1.04:gamma=1.01,"
        "vibrance=0.10,"
        "colorbalance=rs=-0.008:gs=0.004:bs=0.020:rh=0.016:gh=0.004:bh=-0.010")

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("CMD FAIL:\n%s\n---\n%s" % (" ".join(cmd), p.stderr.decode("utf-8", "replace")[-2500:]))
    return p.stderr.decode("utf-8", "replace")

def render_shot(shot, idx):
    src = os.path.join(SRC, shot["file"])
    dur_out = float(shot["dur"]); speed = float(shot.get("speed", 1.0))
    dur_src = dur_out * speed; start = max(0.0, float(shot["start"]))
    vf = ["trim=start=0:duration=%.4f" % (dur_src + 0.05)]
    vf.append("setpts=(PTS-STARTPTS)/%.5f" % speed if abs(speed - 1) > 1e-6 else "setpts=PTS-STARTPTS")
    vf.append("fps=%d" % FPS)
    vf.append("scale=%d:%d:flags=lanczos" % (OUT_W, OUT_H))
    vf.append("setsar=1")
    if shot.get("eqs"):
        vf.append(shot["eqs"])
    vf.append(LOOK)
    out = os.path.join(CLIPS, "shot_%02d.mp4" % idx)
    run([FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
         "-ss", "%.3f" % start, "-i", src,
         "-filter_complex", "[0:v]" + ",".join(vf) + "[v]",
         "-map", "[v]", "-an", "-r", str(FPS),
         "-frames:v", str(int(round(dur_out * FPS))),
         "-c:v", "libx264", "-preset", "medium", "-crf", "15",
         "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", out])
    return out

def assemble(edl, bgm, out_path, opts):
    shots = edl["shots"]; overlays = edl.get("overlays", [])
    n = len(shots)
    total = sum(float(s["dur"]) for s in shots) - sum(float(s.get("trans", 0.0) or 0.0) for s in shots[:-1])
    fc = []
    for i in range(n):
        fc.append("[%d:v]settb=AVTB,setsar=1,format=yuv420p[v%d]" % (i, i))
    cur = "v0"
    for i in range(1, n):
        tr = float(shots[i - 1].get("trans", 0.0) or 0.0)
        if tr > 0.01:
            dur_before = float(shots[i - 1]["dur"])
            off = sum(float(s["dur"]) for s in shots[:i]) - sum(float(s.get("trans", 0.0) or 0.0) for s in shots[:i - 1]) - tr
            name = shots[i - 1].get("trans_type") or "fade"
            fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]" % (cur, i, name, tr, off, i))
            cur = "x%d" % i
        else:
            fc.append("[%s][v%d]concat=n=2:v=1:a=0[c%d]" % (cur, i, i))
            cur = "c%d" % i
    # overlays
    ov_input_start = n + 1          # 0..n-1 shots, n = audio, n+1.. = overlays
    inputs = []
    for i in range(n):
        inputs += ["-i", os.path.join(CLIPS, "shot_%02d.mp4" % i)]
    inputs += ["-i", bgm]
    ov_filter = []
    for k, ov in enumerate(overlays):
        p = os.path.join(GFX, ov["png"])
        a = float(ov["start"]); b = float(ov["start"]) + float(ov["dur"])
        inputs += ["-itsoffset", "%.3f" % a, "-loop", "1", "-framerate", str(FPS),
                   "-t", "%.3f" % (float(ov["dur"]) + 1.5), "-i", p]
        idx = ov_input_start + k
        fade = float(ov.get("fade", 0.45))
        expr = ""
        if ov.get("x_expr"):
            pos = "x='%s':y=%d" % (ov["x_expr"].replace("TOTAL", "%.3f" % total), ov["y"])
        elif ov.get("slide"):
            xexpr = "%d-%d*(1-t/%.3f)" % (ov["x"], ov["w"], total)
            pos = "x='%s':y=%d" % (xexpr, ov["y"])
        else:
            pos = "x=%d:y=%d" % (ov["x"], ov["y"])
        ov_filter.append("[%d:v]format=rgba,fade=t=in:st=%.3f:d=%.3f:alpha=1,fade=t=out:st=%.3f:d=%.3f:alpha=1[ov%d]" %
                         (idx, a, fade, max(a, b - fade), fade, k))
        fc.append("[%s][ov%d]overlay=%s:enable='between(t,%.3f,%.3f)':eof_action=pass:repeatlast=0[g%d]" % (
            cur, k, pos, a, b, k))
        cur = "g%d" % k
    fade_in = float(opts.get("fade_in", 1.0)); fade_out = float(opts.get("fade_out", 2.2))
    fc.append("[%s]fade=t=in:st=0:d=%.3f,fade=t=out:st=%.3f:d=%.3f,format=yuv420p[vout]" % (
        cur, fade_in, total - fade_out, fade_out))
    af_in = float(opts.get("afade_in", 0.6)); af_out = float(opts.get("afade_out", 3.5))
    fc.append("[%d:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,"
              "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
              "afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f,"
              "loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000,apad[aout]" % (
                  n, total, af_in, max(0.0, total - af_out), af_out))
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(ov_filter + fc),
        "-map", "[vout]", "-map", "[aout]", "-t", "%.3f" % total,
        "-r", str(FPS), "-c:v", "libx264", "-preset", "slow",
        "-crf", os.environ.get("CRF", "18"),
        "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
        "-x264-params", "keyint=60:min-keyint=30",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", out_path]
    run(cmd)
    return total

def main():
    edl_path, bgm, out_path, opts_path = sys.argv[1:5]
    edl = json.load(open(edl_path, encoding="utf-8-sig"))
    opts = json.load(open(opts_path, encoding="utf-8-sig")) if os.path.exists(opts_path) else {}
    os.makedirs(CLIPS, exist_ok=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.environ.get("SKIP_SHOTS") != "1":
        for i, s in enumerate(edl["shots"]):
            print("shot %02d %-14s in=%6.2f dur=%4.2f spd=%.2f trans=%.2f %s" % (
                i, s["file"], s["start"], s["dur"], s.get("speed", 1.0),
                s.get("trans", 0.0) or 0.0, s.get("trans_type", "-")))
            render_shot(s, i)
    total = assemble(edl, bgm, out_path, opts)
    print("DONE total=%.3fs -> %s" % (total, out_path))

if __name__ == "__main__":
    main()
