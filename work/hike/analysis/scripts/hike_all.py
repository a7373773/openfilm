# -*- coding: utf-8 -*-
import os, sys, json, glob, time, subprocess, concurrent.futures, argparse
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\hike\analysis"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\immich-20261112_115253"
SCRIPT = os.path.join(OUT, "scripts", "hike_one.py")
PARTS = os.path.join(OUT, "parts")
LOGS = os.path.join(OUT, "logs")

def merge():
    data, meta = {}, {}
    for p in sorted(glob.glob(os.path.join(PARTS, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        data[d["file"]] = d["frames"]
        meta[d["file"]] = {"duration": d["duration"], "n_frames": d["n_frames"]}
    data = dict(sorted(data.items())); meta = dict(sorted(meta.items()))
    for name, obj in (("metrics.json", data), ("meta.json", meta)):
        tmp = os.path.join(OUT, name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
        os.replace(tmp, os.path.join(OUT, name))
    return data, meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--files", nargs="*", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    files = a.files or sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
    log = open(os.path.join(LOGS, "run.log"), "a", encoding="utf-8")
    def say(m):
        s = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
        print(s, flush=True); log.write(s + "\n"); log.flush()
    done = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PARTS, "*.json"))}
    todo = [f for f in files if a.force or os.path.splitext(f)[0] not in done]
    say("files=%d todo=%d workers=%d" % (len(files), len(todo), a.workers))
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(subprocess.run, [sys.executable, SCRIPT, fn], capture_output=True, text=True,
                          encoding="utf-8", errors="replace"): fn for fn in todo}
        for fut in concurrent.futures.as_completed(futs):
            fn = futs[fut]
            p = fut.result()
            out = (p.stdout or "").strip()
            if p.returncode != 0 or "FAIL" in out:
                say("FAIL %s %s" % (fn, (out + p.stderr[-200:])[:300]))
            else:
                say(out)
            merge()
    data, meta = merge()
    say("DONE %d files, %.1fs, frames=%d" % (len(data), time.time()-t0, sum(len(v) for v in data.values())))
    log.close()

if __name__ == "__main__":
    main()
