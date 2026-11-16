
import os, cv2, numpy as np
SRC = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\素材\观澜版画村基地"
OUT = r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\guanlan\sheets"
os.makedirs(OUT, exist_ok=True)
FILES = sorted(f for f in os.listdir(SRC) if f.upper().endswith(".MP4"))
TW = 380
for f in FILES:
    cap = cv2.VideoCapture(os.path.join(SRC,f))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 30
    dur = n/fps
    cols, rows = 4, 3
    cnt = cols*rows
    times = [dur*(i+0.5)/cnt for i in range(cnt)]
    tiles=[]
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t*1000)
        ok, fr = cap.read()
        if not ok: fr = np.zeros((216,TW,3),np.uint8)
        h,w = fr.shape[:2]
        fr = cv2.resize(fr,(TW,int(TW*h/w)))
        cv2.putText(fr, "%.1fs"%t, (8,26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        tiles.append(fr)
    th = tiles[0].shape[0]
    sheet = np.zeros((rows*th, cols*TW, 3), np.uint8)
    for i,tile in enumerate(tiles):
        r,c = divmod(i,cols)
        sheet[r*th:(r+1)*th, c*TW:(c+1)*TW] = tile
    cv2.putText(sheet, f+"  %.1fs %dx%d"%(dur, int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))), (10,th-12) if False else (10, th*1+0), cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,255),2)
    p = os.path.join(OUT, f.replace(".MP4","")+"_sheet.jpg")
    cv2.imwrite(p, sheet, [cv2.IMWRITE_JPEG_QUALITY, 82])
    print(p, sheet.shape, "dur=%.1f"%dur, "fps=%.2f"%fps)
    cap.release()
