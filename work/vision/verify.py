
# -*- coding: utf-8 -*-
import json, os, statistics as st

V = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\vision"
FR = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\analysis\frames"
ok = True
def fail(m):
    global ok
    ok = False
    print("  FAIL:", m)

tags = json.load(open(os.path.join(V,"tags.json"), encoding="utf-8"))
pf = json.load(open(os.path.join(V,"per_file.json"), encoding="utf-8"))
cands = json.load(open(os.path.join(V,"candidates.json"), encoding="utf-8"))
sm = json.load(open(os.path.join(V,"summary.json"), encoding="utf-8"))

print("== tags.json coverage ==")
nframes = 0
for f in sorted(os.listdir(FR)):
    d = os.path.join(FR, f)
    if not os.path.isdir(d): continue
    n = len([x for x in os.listdir(d) if x.endswith(".jpg")])
    key = f + ".mp4"
    if key not in tags:
        fail("missing file %s" % key); continue
    rows = tags[key]
    ts = [r["t"] for r in rows]
    if ts != sorted(ts): fail("%s t not sorted" % key)
    if ts != list(range(1, n+1)): fail("%s t not contiguous 1..%d (got %d..%d, len %d)" % (key, n, ts[0], ts[-1], len(ts)))
    nframes += n
    for r in rows:
        pb = max(r["p_hand"], r["p_fabric"], r["p_closeup"])
        if abs(pb - r["p_blocked"]) > 1e-3:
            fail("%s t=%d p_blocked mismatch %s vs %s" % (key, r["t"], r["p_blocked"], pb)); break
        for k in ["p_landscape","p_hand","p_fabric","p_closeup","p_blurry","scene_p"]:
            if not (0.0 <= r[k] <= 1.0): fail("%s t=%d %s out of range %s" % (key, r["t"], k, r[k]))
print("  files=%d  frames=%d  (frames dir total=%d)" % (len(tags), sum(len(v) for v in tags.values()), nframes))
if sum(len(v) for v in tags.values()) != nframes: fail("frame count mismatch")

print("== per_file.json ==")
need = ["file","frames","mean_p_landscape","median_p_landscape","mean_p_blocked","mean_p_blurry","landscape_ratio","blocked_ratio"]
for r in pf:
    for k in need:
        if k not in r: fail("%s missing %s" % (r["file"], k))
print("  entries=%d  sum frames=%d" % (len(pf), sum(r["frames"] for r in pf)))
if len(pf) != len(tags): fail("per_file count != tags count")

print("== candidates.json constraint re-check ==")
bad = 0
Lall = []
for f in tags:
    Lall += [r["p_landscape"] for r in tags[f]]
Lall_sorted = sorted(Lall)
def pct(v):
    import bisect
    return bisect.bisect_right(Lall_sorted, v)/len(Lall_sorted)
prev = 2.0
for c in cands:
    rows = {r["t"]: r for r in tags[c["file"]]}
    seg = [rows[t] for t in range(c["start_t"], c["end_t"]+1) if t in rows]
    if len(seg) != c["dur"]: fail("%s %d-%d dur mismatch" % (c["file"], c["start_t"], c["end_t"]))
    mL = sum(r["p_landscape"] for r in seg)/len(seg)
    mB = sum(r["p_blocked"] for r in seg)/len(seg)
    med = st.median([r["p_landscape"] for r in tags[c["file"]]])
    if abs(mL - c["mean_p_landscape"]) > 2e-3: fail("%s %d-%d meanL mismatch" % (c["file"], c["start_t"], c["end_t"]))
    if c["dur"] < 3: fail("%s %d-%d dur<3" % (c["file"], c["start_t"], c["end_t"]))
    if mL < med + 0.10 - 1e-6: fail("%s %d-%d meanL %.3f < med %.3f+0.10" % (c["file"], c["start_t"], c["end_t"], mL, med))
    if mB >= 0.35: fail("%s %d-%d meanBlk %.3f >= 0.35" % (c["file"], c["start_t"], c["end_t"], mB))
    if c["mean_p_landscape"] > prev + 1e-9: fail("not sorted desc at %s" % c["file"])
    prev = c["mean_p_landscape"]
    if seg[0]["t"] > 1:
        left = rows.get(c["start_t"]-1)
        if left and left["p_landscape"] >= med + 0.10 and left["p_blocked"] < 0.35:
            fail("segment %s %d-%d not maximal (left neighbour qualifies)" % (c["file"], c["start_t"], c["end_t"]))
print("  candidates=%d  secs=%d  all constraints checked" % (len(cands), sum(c["dur"] for c in cands)))

print("== blocked segments ==")
bs = sm["blocked_segments"]
print("  segments=%d  secs=%d" % (len(bs), sum(b["dur"] for b in bs)))
for b in bs:
    if b["dur"] < 2: fail("blocked seg <2s %s %d-%d" % (b["file"], b["start_t"], b["end_t"]))
    rows = {r["t"]: r for r in tags[b["file"]]}
    seg = [rows[t] for t in range(b["start_t"], b["end_t"]+1) if t in rows]
    if any(r["p_blocked"] <= 0.5 for r in seg): fail("blocked seg contains low frames %s %d-%d" % (b["file"], b["start_t"], b["end_t"]))
    if b["start_t"] > 1 and rows.get(b["start_t"]-1, {}).get("p_blocked", 0) > 0.5: fail("blocked seg not maximal %s" % b["file"])

print("== reference numbers ==")
ge05 = sum(1 for v in Lall if v >= 0.5); ge03 = sum(1 for v in Lall if v >= 0.3)
print("  p_landscape>=0.5: %d (%.1f%%) | >=0.3: %d (%.1f%%) | mean %.4f | n %d" % (ge05, 100*ge05/len(Lall), ge03, 100*ge03/len(Lall), sum(Lall)/len(Lall), len(Lall)))
print("  summary says: ge05=%d ge03=%d" % (sm["landscape_ge_05"], sm["landscape_ge_03"]))
print("\nRESULT:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
