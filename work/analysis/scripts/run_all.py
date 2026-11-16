# -*- coding: utf-8 -*-
"""Orchestrator: run analyze_one.py on all clips with N parallel workers, merge metrics.json incrementally."""
import os, sys, json, glob, time, subprocess, concurrent.futures, argparse

OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis"
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材"
SCRIPT = os.path.join(OUT, "scripts", "analyze_one.py")
PARTS = os.path.join(OUT, "parts")
LOGS = os.path.join(OUT, "logs")

def merge_metrics():
    data, meta = {}, {}
    for p in sorted(glob.glob(os.path.join(PARTS, "*.json"))):
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        data[d["file"]] = d["frames"]
        meta[d["file"]] = {"duration": d["duration"], "n_frames": d["n_frames"], "rows": d["rows"], "sheet": d["sheet"]}
    data = dict(sorted(data.items()))
    meta = dict(sorted(meta.items()))
    for name, obj in (("metrics.json", data), ("meta.json", meta)):
        tmp = os.path.join(OUT, name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False)
        os.replace(tmp, os.path.join(OUT, name))
    return data, meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--files", nargs="*", default=None)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(LOGS, exist_ok=True)
    if a.files:
        files = a.files
    else:
        files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp4"))
    log = open(os.path.join(LOGS, "run.log"), "a", encoding="utf-8")
    def say(msg):
        line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        log.write(line + "\n"); log.flush()
    done_parts = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(PARTS, "*.json"))}
    todo = [f for f in files if a.force or os.path.splitext(f)[0] not in done_parts]
    say("files=%d  todo=%d  workers=%d  (already done: %d)" % (len(files), len(todo), a.workers, len(done_parts)))
    t_start = time.time()
    if not todo:
        merge_metrics(); say("nothing to do"); return
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {}
        for fn in todo:
            cmd = [sys.executable, SCRIPT, fn] + (["--force"] if a.force else [])
            futs[ex.submit(subprocess.run, cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")] = fn
        for fut in concurrent.futures.as_completed(futs):
            fn = futs[fut]
            try:
                p = fut.result()
                out = (p.stdout or "").strip() + (" | ERR:" + (p.stderr or "").strip()[-300:] if p.stderr.strip() else "")
                if p.returncode != 0 or "FAIL" in out:
                    say("FAIL %s -> %s" % (fn, out[:400]))
                else:
                    say(out.replace("\n", " | "))
            except Exception as e:
                say("EXC %s %r" % (fn, e))
            data, meta = merge_metrics()
            say("  merged: %d/%d files in metrics.json (%.1fs elapsed)" % (len(data), len(files), time.time()-t_start))
    data, meta = merge_metrics()
    say("DONE %d files, %.0fs total" % (len(data), time.time()-t_start))
    log.close()

if __name__ == "__main__":
    main()
