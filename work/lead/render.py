# -*- coding: utf-8 -*-
"""openfilm montage renderer v2: EDL -> graded 1080p30 shots -> xfade assembly + BGM."""
import json, os, subprocess, sys

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
SRC = os.path.join(ROOT, "素材")
WORK = os.path.join(ROOT, "work")
CLIPS = os.path.join(WORK, "clips")
RENDER = os.path.join(WORK, "render")
OUT_W, OUT_H, FPS = 1920, 1080, 30

# ---- the look (calibrated numerically) ----
LOOK = ("curves=all='0/0.010 0.25/0.255 0.5/0.525 0.80/0.800 1/0.920',"
        "eq=saturation=1.02:contrast=1.02,"
        "vibrance=0.08,"
        "colorbalance=rs=-0.012:bs=0.028:rh=0.025:bh=-0.012")

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("CMD FAIL:\n%s\n---\n%s" % (" ".join(cmd), p.stderr.decode("utf-8", "replace")[-2500:]))
    return p.stderr.decode("utf-8", "replace")

def levels_filter(lv):
    if not lv: return []
    rmin, rmax, gmin, gmax, bmin, bmax = [float(x) for x in lv]
    return ["colorlevels=rimin=%.4f:rimax=%.4f:gimin=%.4f:gimax=%.4f:bimin=%.4f:bimax=%.4f" %
            (rmin, rmax, gmin, gmax, bmin, bmax)]

def render_shot(shot, idx):
    src = os.path.join(SRC, shot["file"])
    dur_out = float(shot["dur"])
    speed = float(shot.get("speed", 1.0))
    dur_src = dur_out * speed
    start = max(0.0, float(shot["start"]))
    vf = ["trim=start=0:duration=%.4f" % (dur_src + 0.05)]
    if abs(speed - 1.0) > 1e-6:
        vf.append("setpts=(PTS-STARTPTS)/%.5f" % speed)
    else:
        vf.append("setpts=PTS-STARTPTS")
    vf.append("fps=%d" % FPS)
    vf.append("scale=%d:%d:flags=lanczos" % (OUT_W, OUT_H))
    vf.append("setsar=1")
    vf += levels_filter(shot.get("levels"))
    vf.append(LOOK)
    out = os.path.join(CLIPS, "shot_%02d.mp4" % idx)
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
           "-ss", "%.3f" % start, "-i", src,
           "-filter_complex", "[0:v]" + ",".join(vf) + "[v]",
           "-map", "[v]", "-an", "-r", str(FPS),
           "-frames:v", str(int(round(dur_out * FPS))),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "13",
           "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
           out]
    run(cmd)
    return out

def assemble(edl, bgm, out_path, opts):
    shots = edl["shots"]
    n = len(shots)
    xf = [float(s.get("xfade", 0.0)) for s in shots]
    durations = [float(s["dur"]) for s in shots]
    fc = []
    for i in range(n):
        fc.append("[%d:v]settb=AVTB,setsar=1,format=yuv420p[v%d]" % (i, i))
    cur = "v0"; acc = durations[0]
    for i in range(1, n):
        d = xf[i-1]
        off = acc - d
        fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]" % (
            cur, i, shots[i].get("transition", "fade"), d, off, i))
        acc = acc + durations[i] - d
        cur = "x%d" % i
    total = acc
    fade_in = float(opts.get("fade_in", 1.0))
    fade_out = float(opts.get("fade_out", 1.8))
    fc.append("[%s]fade=t=in:st=0:d=%.3f,fade=t=out:st=%.3f:d=%.3f,format=yuv420p[vf]" % (
        cur, fade_in, total - fade_out, fade_out))
    afade_in = float(opts.get("afade_in", 0.8))
    afade_out = float(opts.get("afade_out", 3.0))
    fc.append("[%d:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,"
              "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
              "afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f,"
              "loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad[aout]" % (
                  n, total, afade_in, max(0.0, total - afade_out), afade_out))
    inputs = []
    for i in range(n):
        inputs += ["-i", os.path.join(CLIPS, "shot_%02d.mp4" % i)]
    inputs += ["-i", bgm]
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(fc),
        "-map", "[vf]", "-map", "[aout]",
        "-t", "%.3f" % total,
        "-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "18"),
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-x264-params", "keyint=60:min-keyint=30:scenecut=0",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", out_path]
    run(cmd)
    return total

def main():
    edl_path, bgm, out_path, opts_path = sys.argv[1:5]
    edl = json.load(open(edl_path, encoding="utf-8-sig"))
    opts = json.load(open(opts_path, encoding="utf-8-sig")) if os.path.exists(opts_path) else {}
    os.makedirs(CLIPS, exist_ok=True); os.makedirs(RENDER, exist_ok=True)
    only = os.environ.get("ONLY_SHOT")
    skip = os.environ.get("SKIP_SHOTS") == "1"
    for i, s in enumerate(edl["shots"]):
        if skip: break
        if only is not None and int(only) != i: continue
        print("shot %02d %-16s start=%7.2f dur=%4.2f speed=%.2f" % (i, s["file"], s["start"], s["dur"], s.get("speed", 1.0)))
        render_shot(s, i)
    total = assemble(edl, bgm, out_path, opts)
    print("DONE total=%.3fs -> %s" % (total, out_path))

if __name__ == "__main__":
    main()
