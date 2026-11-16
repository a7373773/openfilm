# -*- coding: utf-8 -*-
"""openfilm / zhongshan renderer: shots -> xfade assembly -> music -> titles."""
import json, os, subprocess, sys, shutil
from concurrent.futures import ThreadPoolExecutor
sys.stdout.reconfigure(encoding="utf-8")

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
SRC = os.path.join(ROOT, "素材", "中山")
WORK = os.path.join(ROOT, "work", "zs")
CLIPS = os.path.join(WORK, "clips"); os.makedirs(CLIPS, exist_ok=True)
EDL = json.load(open(os.path.join(WORK, "edl.json"), encoding="utf-8"))
W, H, FPS = 1920, 1080, 30
TOTAL = EDL["total"]

def run(cmd, label=""):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("FAIL %s\n%s\n---\n%s" % (label, " ".join(cmd)[:1200],
                           p.stderr.decode("utf-8", "replace")[-2000:]))
    return p.stderr.decode("utf-8", "replace")

def grade(sh):
    w = float(sh["warm"])
    p2, p50, p98 = float(sh["p2"]), float(sh["p50"]), float(sh["p98"])
    imin = max(0.0, p2/255.0*0.55)
    imax = min(1.0, 1.0 - (1.0 - p98/255.0)*0.30)
    db = max(-0.035, min(0.035, ((0.42*255 - p50)/255.0)*0.30))
    rh = 0.020 + 0.026*w; bh = -0.014 - 0.018*w
    rs = -0.006 - 0.004*w; bs = 0.010 + 0.004*w
    return ",".join([
        "colorlevels=rimin=%.3f:rimax=%.3f:gimin=%.3f:gimax=%.3f:bimin=%.3f:bimax=%.3f" % (imin, imax, imin, imax, imin, imax),
        "eq=brightness=%.3f:contrast=1.03:saturation=1.05" % db,
        "curves=all='0/0.012 0.25/0.262 0.5/0.53 0.78/0.788 1/0.945'",
        "vibrance=intensity=0.13",
        "colorbalance=rs=%.3f:bs=%.3f:rh=%.3f:bh=%.3f" % (rs, bs, rh, bh),
        "unsharp=5:5:0.30:5:5:0",
    ])

def render_shot(sh, crf=15):
    out = os.path.join(CLIPS, "shot_%02d.mp4" % sh["i"])
    outdur = sh["dur"]; speed = sh["speed"]; d_src = sh["src"]
    vf = ["setpts=(PTS-STARTPTS)/%.4f" % speed if abs(speed-1.0) > 1e-4 else "setpts=PTS-STARTPTS",
          "fps=%d" % FPS,
          "scale=%d:%d:force_original_aspect_ratio=increase:flags=lanczos" % (W, H),
          "crop=%d:%d" % (W, H), "setsar=1", grade(sh)]
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
           "-ss", "%.3f" % sh["start"], "-t", "%.3f" % (d_src + 0.5),
           "-i", os.path.join(SRC, sh["file"]),
           "-vf", ",".join(vf), "-an", "-r", str(FPS),
           "-frames:v", str(int(round(outdur*FPS))),
           "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-g", "60", "-sc_threshold", "0", out]
    run(cmd, "shot%02d" % sh["i"])
    return out

def step_clips(sel=None):
    shots = [s for s in EDL["shots"] if sel is None or s["i"] in sel]
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(render_shot, shots))
    print("clips ok", len(shots))

def step_assemble(crf=15):
    shots = EDL["shots"]
    pos, t = [], 0.0
    for s in shots:
        pos.append(round(t, 4)); t += s["dur"] - s["xfd"]
    inputs = []
    for s in shots:
        inputs += ["-i", os.path.join(CLIPS, "shot_%02d.mp4" % s["i"])]
    bgm = os.path.join(WORK, "bgm.wav")
    inputs += ["-i", bgm]
    fc = []
    for s in shots:
        fc.append("[%d:v]settb=AVTB,setpts=PTS-STARTPTS,fps=%d,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1[v%d]" % (s["i"], FPS, W, H, W, H, s["i"]))
    cur = "v0"
    for i in range(1, len(shots)):
        nxt = "x%d" % i
        off = max(0.0, pos[i] - 0.002)
        fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[%s]" % (
            cur, i, shots[i]["xf"], shots[i]["xfd"], off, nxt))
        cur = nxt
    ass = "C\\:/Users/30308/AppData/Local/Temp/zs_titles.ass"
    fc.append("[%s]subtitles='%s':fontsdir='C\\:/Windows/Fonts',fade=t=in:st=0:d=1.0,fade=t=out:st=%.2f:d=1.6,format=yuv420p[vout]" % (
        cur, ass, TOTAL - 1.6))
    fc.append("[%d:a]atrim=0:%.3f,asetpts=PTS-STARTPTS[aout]" % (len(shots), TOTAL))
    out = os.path.join(WORK, "zhongshan_master.mp4")
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-r", str(FPS), "-t", "%.3f" % TOTAL,
        "-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    run(cmd, "assemble")
    print("master ok", out, os.path.getsize(out))

def main():
    step = sys.argv[1] if len(sys.argv) > 1 else "clips"
    if step == "clips": step_clips()
    elif step == "test":
        ids = [int(x) for x in sys.argv[2].split(",")]
        step_clips(set(ids))
    elif step == "assemble": step_assemble(int(sys.argv[2]) if len(sys.argv)>2 else 15)

if __name__ == "__main__":
    main()