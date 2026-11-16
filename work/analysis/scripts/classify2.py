# -*- coding: utf-8 -*-
import json, os, math, statistics as st
OUT = "D:/BaiduSyncdisk/工作/PMMaster/openfilm/work/analysis"
D = json.load(open(os.path.join(OUT,"metrics.json"), encoding="utf-8"))
def pct(a,p):
    s=sorted(a); k=(len(s)-1)*p; f=int(math.floor(k)); c=min(f+1,len(s)-1)
    return s[f]+(s[c]-s[f])*(k-f)
def classify(fr):
    n=len(fr)
    PS=max(pct([f["sharp"] for f in fr],0.90),1.0)
    PE=max(pct([f["edgefrac"] for f in fr],0.90),0.001)
    lab=[None]*n; det=[0.0]*n; er=[0.0]*n
    for i,f in enumerate(fr):
        d=f["sharp"]/PS; e=f["edgefrac"]/PE
        det[i]=d; er[i]=e
        if f["luma"]<35 or f["darkfrac"]>0.70: lab[i]="BLACK"
        elif f["luma"]>240 or f["brightfrac"]>0.80: lab[i]="WHITE"
        elif (e<0.15 and d<0.15): lab[i]="BLOCK"
        elif (d<0.25 and e<0.45 and f["lumastd"]>=32 and f["uniform"]<0.45): lab[i]="BLUR"
        elif (f["uniform"]>0.45 or f["lumastd"]<25): lab[i]="FLATS"
    return lab,det,er,PS,PE
def runs(lab):
    n=len(lab); out=[]; i=0
    while i<n:
        if lab[i]:
            j=i
            while j+1<n and lab[j+1]==lab[i]: j+=1
            out.append((i,j,lab[i])); i=j+1
        else: i+=1
    return out
tot=0
for fn in sorted(D):
    fr=D[fn]; lab,det,er,PS,PE=classify(fr)
    n=len(fr); tot+=n
    cnt={}
    for l in lab:
        if l: cnt[l]=cnt.get(l,0)+1
    rs=runs(lab)
    print("%-14s n=%3d P90sharp=%6.0f P90edge=%.2f  flagged=%s" % (fn,n,PS,PE,cnt or "none"))
    for a,b,l in rs:
        seg=fr[a:b+1]
        print("    %s %3d-%3d (%2d s) det=%.2f e=%.2f uni=%.2f std=%4.1f luma=%4.0f colf=%4.1f ent=%.2f dif=%.0f" % (
            l,a,b+1,b-a+1, st.mean([det[k] for k in range(a,b+1)]), st.mean([er[k] for k in range(a,b+1)]),
            st.mean([fr[k]["uniform"] for k in range(a,b+1)]), st.mean([fr[k]["lumastd"] for k in range(a,b+1)]),
            st.mean([fr[k]["luma"] for k in range(a,b+1)]), st.mean([fr[k]["colorful"] for k in range(a,b+1)]),
            st.mean([fr[k]["entropy"] for k in range(a,b+1)]), st.mean([fr[k]["diff"] for k in range(a,b+1)])))
print("total frames", tot)
