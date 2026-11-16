
# -*- coding: utf-8 -*-
"""一版秋花 — EDL -> graded shots -> xfade assembly + BGM + paper cards."""
import json, os, subprocess, sys

FF = r"C:\Users\30308\AppData\Local\Programs\Python\Python314\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"
ROOT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm"
SRC = os.path.join(ROOT, "素材", "观澜版画村基地")
WK = os.path.join(ROOT, "work", "guanlan")
CLIPS = os.path.join(WK, "clips")
GFX = os.path.join(WK, "gfx")
OUT_W, OUT_H, FPS = 1920, 1080, 30

# 印刷纸感调色：高光回收、绿稍降、暗部微青、高光微暖
GRADE = ("curves=r='0/0.010 0.5/0.505 0.85/0.845 1/0.905'"
         ":g='0/0.010 0.5/0.480 0.85/0.830 1/0.900'"
         ":b='0/0.014 0.5/0.515 0.85/0.850 1/0.910',"
         "eq=saturation=0.95:contrast=1.04,vibrance=0.14,"
         "colorbalance=rs=-0.010:bs=0.016:rh=0.014:bh=-0.010,"
         "unsharp=5:5:0.45:5:5:0,"
         "noise=alls=6:allf=t,vignette=angle=PI/6")

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise RuntimeError("CMD FAIL:\n%s\n---\n%s" % (" ".join(cmd), p.stderr.decode("utf-8", "replace")[-2500:]))
    return p.stderr.decode("utf-8", "replace")

def render_shot(shot, idx):
    dur_out = float(shot["dur"])
    out = os.path.join(CLIPS, "shot_%02d.mp4" % idx)
    if shot.get("still"):
        vf = ("scale=%d:%d:flags=lanczos,setsar=1,fps=%d,format=yuv420p" % (OUT_W, OUT_H, FPS))
        run([FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
             "-loop", "1", "-framerate", str(FPS), "-t", "%.3f" % (dur_out + 0.2),
             "-i", os.path.join(GFX, shot["still"]),
             "-vf", vf, "-r", str(FPS), "-frames:v", str(int(round(dur_out * FPS))),
             "-c:v", "libx264", "-preset", "medium", "-crf", "14",
             "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", out])
        return out
    if shot.get("zoom"):
        return render_dolly(shot, idx)
    src = os.path.join(SRC, shot["file"])
    speed = float(shot.get("speed", 1.0))
    dur_src = dur_out * speed
    start = max(0.0, float(shot["start"]))
    vf = ["trim=start=0:duration=%.4f" % (dur_src + 0.10)]
    vf.append("setpts=(PTS-STARTPTS)/%.5f" % speed if abs(speed - 1) > 1e-6 else "setpts=PTS-STARTPTS")
    vf.append("fps=%d" % FPS)
    vf.append("scale=%d:%d:flags=lanczos" % (OUT_W, OUT_H))
    vf.append("setsar=1")
    if shot.get("eqs"):
        vf.append(shot["eqs"])
    vf.append(GRADE)
    vf.append("format=yuv420p")
    run([FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
         "-ss", "%.3f" % start, "-i", src,
         "-filter_complex", "[0:v]" + ",".join(vf) + "[v]",
         "-map", "[v]", "-an", "-r", str(FPS),
         "-frames:v", str(int(round(dur_out * FPS))),
         "-c:v", "libx264", "-preset", "medium", "-crf", "14",
         "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0", out])
    return out


def render_dolly(shot, idx):
    """亚像素缓推：ffmpeg 解码 -> cv2 亚像素缩放 -> ffmpeg 调色编码，无阶梯感。"""
    import numpy as np, cv2
    src = os.path.join(SRC, shot["file"])
    dur_out = float(shot["dur"]); speed = float(shot.get("speed", 1.0))
    start = max(0.0, float(shot["start"]))
    n = int(round(dur_out * FPS))
    z0, z1 = [float(v) for v in shot["zoom"]]
    dec = [FF, "-hide_banner", "-nostdin", "-loglevel", "error",
           "-ss", "%.3f" % start, "-t", "%.3f" % (dur_out * speed + 0.1), "-i", src,
           "-vf", "setpts=(PTS-STARTPTS)/%.5f,fps=%d,scale=%d:%d:flags=lanczos" % (speed, FPS, OUT_W, OUT_H),
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    enc = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (OUT_W, OUT_H), "-r", str(FPS), "-i", "-",
           "-vf", GRADE + ",format=yuv420p", "-frames:v", str(n),
           "-c:v", "libx264", "-preset", "medium", "-crf", "14",
           "-pix_fmt", "yuv420p", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
           os.path.join(CLIPS, "shot_%02d.mp4" % idx)]
    p1 = subprocess.Popen(dec, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    p2 = subprocess.Popen(enc, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    fs = OUT_W * OUT_H * 3
    cx, cy = OUT_W / 2.0, OUT_H / 2.0
    i = 0
    last = None
    try:
        while i < n:
            buf = p1.stdout.read(fs)
            if len(buf) < fs:
                if last is not None:
                    while i < n:
                        p2.stdin.write(last); i += 1
                break
            last = buf
            fr = np.frombuffer(buf, np.uint8).reshape(OUT_H, OUT_W, 3)
            u = i / max(1, n - 1)
            e = u * u * (3 - 2 * u)          # smoothstep 缓入缓出
            z = z0 + (z1 - z0) * e
            s = 1.0 / z
            M = np.array([[s, 0, cx * (1 - s)], [0, s, cy * (1 - s)]], np.float32)
            out_fr = cv2.warpAffine(fr, M, (OUT_W, OUT_H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
            last = out_fr.tobytes()
            p2.stdin.write(last)
            i += 1
    finally:
        p1.stdout.close(); p1.wait()
        try:
            p2.stdin.close()
        except Exception:
            pass
        err = p2.stderr.read().decode("utf-8", "replace")
        p2.wait()
    if i < n:
        raise RuntimeError("dolly short: got %d/%d frames\n%s" % (i, n, err[-1500:]))
    return os.path.join(CLIPS, "shot_%02d.mp4" % idx)

def assemble(edl, bgm, audio_ss, out_path, opts):
    shots = edl["shots"]; n = len(shots)
    fc = []
    for i in range(n):
        fc.append("[%d:v]settb=AVTB,setsar=1,format=yuv420p[v%d]" % (i, i))
    cur = "v0"; acc = float(shots[0]["dur"])
    for i in range(1, n):
        tr = float(shots[i - 1].get("trans", 0.0) or 0.0)
        typ = shots[i - 1].get("trans_type", "fade")
        if tr > 0.02:
            off = acc - tr
            fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]" % (cur, i, typ, tr, off, i))
            cur = "x%d" % i
        else:
            fc.append("[%s][v%d]concat=n=2:v=1:a=0[c%d]" % (cur, i, i))
            cur = "c%d" % i
        acc = acc + float(shots[i]["dur"]) - tr
    total = acc
    fi = float(opts.get("fade_in", 0.9)); fo = float(opts.get("fade_out", 1.0))
    fc.append("[%s]fade=t=in:st=0:d=%.3f,fade=t=out:st=%.3f:d=%.3f,format=yuv420p[vout]" % (
        cur, fi, total - fo, fo))
    ai = float(opts.get("afade_in", 1.2)); ao = float(opts.get("afade_out", 3.0))
    fc.append("[%d:a]atrim=0:%.3f,asetpts=PTS-STARTPTS,"
              "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
              "afade=t=in:st=0:d=%.3f,afade=t=out:st=%.3f:d=%.3f,"
              "loudnorm=I=-15:TP=-1.5:LRA=9,aresample=48000,apad[aout]" % (
                  n, total, ai, max(0.0, total - ao), ao))
    inputs = []
    for i in range(n):
        inputs += ["-i", os.path.join(CLIPS, "shot_%02d.mp4" % i)]
    inputs += ["-ss", "%.3f" % audio_ss, "-i", bgm]
    cmd = [FF, "-hide_banner", "-nostdin", "-y", "-loglevel", "error"] + inputs + [
        "-filter_complex", ";".join(fc),
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
    edl_path, out_path = sys.argv[1], sys.argv[2]
    bgm = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, "work", "music", "src", "Cattails.mp3")
    audio_ss = float(os.environ.get("AUDIO_SS", "0.40"))
    opts_path = os.path.join(WK, "opts.json")
    edl = json.load(open(edl_path, encoding="utf-8-sig"))
    opts = json.load(open(opts_path, encoding="utf-8-sig")) if os.path.exists(opts_path) else {}
    os.makedirs(CLIPS, exist_ok=True); os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if os.environ.get("SKIP_SHOTS") != "1":
        for i, s in enumerate(edl["shots"]):
            print("shot %02d %-16s in=%5.2f spd=%.2f dur=%5.3f trans=%.2f" % (
                i, s.get("file") or s.get("still"), s.get("start", 0), s.get("speed", 1.0), s["dur"], s.get("trans", 0) or 0))
            sys.stdout.flush()
            render_shot(s, i)
    total = assemble(edl, bgm, audio_ss, out_path, opts)
    print("DONE total=%.3fs -> %s" % (total, out_path))

if __name__ == "__main__":
    main()
