# -*- coding: utf-8 -*-
"""04_grade: the house look, hard-bounded so it never becomes a filter.
Grade = exposure align + highlight rolloff + gentle warm ramp. No LUT."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import RULES

def budget():
    g = RULES["grade"]
    return dict(sat=1.06, vib=0.13, con=1.03, warm_hi=0.030, teal_sh=0.012)  # current house settings
    # bounds enforced in check()

def check(b):
    g = RULES["grade"]; bad = []
    if b["sat"] > g["saturation_max"]: bad.append("saturation %.3f > %.2f" % (b["sat"], g["saturation_max"]))
    if b["vib"] > g["vibrance_max"]: bad.append("vibrance %.3f > %.2f" % (b["vib"], g["vibrance_max"]))
    if b["con"] > g["contrast_max"]: bad.append("contrast %.3f > %.2f" % (b["con"], g["contrast_max"]))
    if b["warm_hi"] > g["highlight_warm_max"]: bad.append("highlight warm %.3f > %.2f" % (b["warm_hi"], g["highlight_warm_max"]))
    if b["teal_sh"] > g["shadow_teal_max"]: bad.append("shadow teal %.3f > %.2f" % (b["teal_sh"], g["shadow_teal_max"]))
    if g.get("lut"): bad.append("LUT forbidden")
    return bad

def filters(p2, p50, p98, warm):
    """warm: 0..1 timeline position -> warmth ramp (daylight keeps its own temperature)."""
    b = budget()
    imin = max(0.0, p2/255.0*0.55)
    imax = min(1.0, 1.0 - (1.0 - p98/255.0)*0.30)
    db = max(-0.035, min(0.035, ((0.42*255 - p50)/255.0)*0.30))
    rh = 0.020 + 0.026*warm; bh = -0.014 - 0.018*warm
    rs = -0.006 - 0.004*warm; bs = 0.010 + 0.004*warm
    return ",".join([
        "colorlevels=rimin=%.3f:rimax=%.3f:gimin=%.3f:gimax=%.3f:bimin=%.3f:bimax=%.3f" % (imin, imax, imin, imax, imin, imax),
        "eq=brightness=%.3f:contrast=%.3f:saturation=%.3f" % (db, b["con"], b["sat"]),
        "curves=all='0/0.012 0.25/0.262 0.5/0.53 0.78/0.788 1/0.945'",
        "vibrance=intensity=%.3f" % b["vib"],
        "colorbalance=rs=%.3f:bs=%.3f:rh=%.3f:bh=%.3f" % (rs, bs, rh, bh),
        "unsharp=5:5:0.30:5:5:0",
    ])

if __name__ == "__main__":
    print("house grade budget:", budget())
    bad = check(budget())
    print("violations:", bad or "none")
    print("sample filter (mid-tone, warm=0.5):")
    print(filters(40, 130, 250, 0.5))
