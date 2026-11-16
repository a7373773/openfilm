# -*- coding: utf-8 -*-
"""03_check: hard gate. Fails loudly instead of shipping a bad cut.
usage: python 03_check.py <edl.json> [index.json]"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

EDLP = sys.argv[1]
edl = json.load(open(EDLP, encoding="utf-8"))
shots = edl["shots"]; T = edl["total"]
idx = None
p = os.path.join(os.path.dirname(EDLP), "index.json")
if os.path.exists(p): idx = json.load(open(p, encoding="utf-8"))
by_file = {c["file"]: c for c in idx["clips"]} if idx else {}
cluster_of = {}
if idx:
    for cl in idx["clusters"]:
        for m in cl["members"]: cluster_of[m] = cl["id"]

fails, warns = [], []
def fail(code, msg): fails.append("[FAIL] %-22s %s" % (code, msg))
def warn(code, msg): warns.append("[WARN] %-22s %s" % (code, msg))

# --- 1. aspect / rotation gate ---
for s in shots:
    c = by_file.get(s["file"])
    if c is None: continue
    if c.get("aspect") != "landscape": fail("ASPECT", "%s is %s (rot=%.0f)" % (s["file"], c["aspect"], c.get("rot", 0)))
    if (c.get("w"), c.get("h")) != tuple(RULES["aspect"]["target"]): fail("SIZE", "%s is %sx%s" % (s["file"], c.get("w"), c.get("h")))

# --- 2. duplicate footage / duplicate subject ---
files = [s["file"] for s in shots]
dup = {f for f in files if files.count(f) > 1}
if dup: fail("DUP_FILE", "same clip used twice: %s" % sorted(dup))
csize = {cl["id"]: len(cl["members"]) for cl in (idx["clusters"] if idx else [])}
same = {}
for i, f in enumerate(files):
    cid = cluster_of.get(f)
    if cid is not None: same.setdefault(cid, []).append(i)
for cid, lst in sorted(same.items()):
    n_use, size = len(lst), csize.get(cid, 1)
    where = ", ".join("%d:%s" % (i, files[i]) for i in lst)
    if size <= 3 and n_use > 1:
        fail("DUP_TIGHT", "cluster C%02d (near-identical, n=%d) used %d times: %s" % (cid, size, n_use, where))
    elif n_use > RULES["dedupe"]["max_same_cluster"]:
        warn("DUP_SUBJECT", "cluster C%02d used %d times (advisory max %d): %s" % (cid, n_use, RULES["dedupe"]["max_same_cluster"], where))
    elif n_use > 1:
        warn("DUP_LOOSE", "cluster C%02d used %d times (loose scene, n=%d): %s" % (cid, n_use, size, where))
    for a, b in zip(lst, lst[1:]):
        if pos_gap(edl, a, b) < RULES["dedupe"]["min_gap_s"]:
            warn("DUP_GAP", "cluster C%02d shots %d/%d closer than %ss" % (cid, a, b, RULES["dedupe"]["min_gap_s"]))

# --- 3. quality floor ---
for s in shots:
    c = by_file.get(s["file"])
    if c and c.get("sharp", 1e9) < RULES["quality"]["min_sharp"] and c.get("sat", 0) > 40:
        warn("QUALITY", "%s sharp=%.0f low" % (s["file"], c["sharp"]))

# --- 4. beat grid (uses the EDL's own beat unit, so re-timed cuts stay valid) ---
BEAT = float(edl.get("beat", RULES["beat"]["beat_unit_s"]))
for s in shots:
    n = s["dur"] / BEAT
    if abs(n - round(n)) > 0.02: fail("BEAT", "%s dur=%.3f not on %.3fs grid" % (s["file"], s["dur"], BEAT))

# --- 5. transition mix ---
dirs = [s for s in shots[1:] if s["xf"] != RULES["transitions"]["default"]]
ratio = len(dirs) / max(1, len(shots)-1)
if ratio > RULES["transitions"]["directional_ratio_max"] + 0.05:
    fail("TRANSITIONS", "non-default transitions %.0f%% > %.0f%%" % (ratio*100, RULES["transitions"]["directional_ratio_max"]*100))
for s in shots:
    if s["xf"] not in RULES["transitions"]["allowed"]: fail("TRANSITION_TYPE", "%s uses %s" % (s["file"], s["xf"]))

# --- 6. grade budget ---
miss = [k for k in ("saturation_max", "vibrance_max", "contrast_max", "highlight_warm_max", "shadow_teal_max") if k not in RULES["grade"]]
if miss: fail("GRADE_RULES", "missing grade budget keys: %s" % miss)

# --- 7. duration ---
if not (RULES["duration"]["min_s"] <= T <= RULES["duration"]["max_s"]):
    fail("DURATION", "%.1fs outside %s-%ss" % (T, RULES["duration"]["min_s"], RULES["duration"]["max_s"]))

# --- 8. music (if bgm present, check loudness / length) ---
bgm = os.path.join(os.path.dirname(EDLP), "bgm.wav")
if os.path.exists(bgm):
    r = subprocess.run([FF, "-hide_banner", "-i", bgm, "-af", "volumedetect", "-f", "null", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE).stderr.decode("utf-8", "replace")
    import re as _re
    m = _re.search(r"mean_volume:\s+([-\d.]+) dB", r)
    if m:
        mv = float(m.group(1))
        if not (-26 <= mv <= -12): warn("MUSIC_LOUD", "mean %.1f dB outside -26..-12" % mv)
else:
    warn("MUSIC", "no bgm.wav next to edl")

print("=" * 64)
print("GATE  %s  |  shots %d  |  %.2fs = %s" % (os.path.basename(EDLP), len(shots), T, mmss(T)))
print("=" * 64)
for w in warns: print(w)
for f in fails: print(f)
print("-" * 64)
print("RESULT:", "PASS" if not fails else "FAIL (%d)" % len(fails))
sys.exit(1 if fails else 0)