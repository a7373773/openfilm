# -*- coding: utf-8 -*-
"""Recompute all metrics from frames already on disk (no decode), then rebuild metrics.json."""
import os, sys, json, time, concurrent.futures
sys.path.insert(0, "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis/scripts")
import analyze_one as A
import run_all as R

def one(fn):
    t0 = time.time()
    o = A.metrics_only(fn)
    return fn, o["n_frames"], time.time()-t0

if __name__ == "__main__":
    meta = json.load(open(os.path.join(A.OUT, "meta.json"), encoding="utf-8"))
    files = sorted(meta.keys())
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for fn, n, dt in ex.map(one, files):
            print("OK %-18s frames=%d %.1fs" % (fn, n, dt), flush=True)
    data, meta2 = R.merge_metrics()
    print("merged %d files in %.1fs" % (len(data), time.time()-t0))
