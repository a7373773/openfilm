
import urllib.request, ssl, os, json
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
OUT=r"D:\BaiduSyncdisk\工作\PMMaster\openfilm\work\music\probe"
os.makedirs(OUT, exist_ok=True)
names = ["Carefree","Life of Riley","Wallpaper","Cipher","Deliberate Thought","Ascending the Vale",
         "Enchanted Valley","Silver Blue Light","Floating Cities","Whispering Stream","Serenity",
         "Dreamy Flashback","Airport Lounge","Bumbly March","Sappheiros","Rite of Passage",
         "Sincerely","Easy Lemon","Achaidh Cheide","Montauk Point","Frost Waltz","Open Sea",
         "Chill Wave","Gymnopedie No 1","Peaceful","Wistful Harp","Bittersweet","Meditation Impromptu 01"]
res={}
for n in names:
    u="https://incompetech.com/music/royalty-free/mp3-royaltyfree/"+urllib.parse.quote(n)+".mp3"
    try:
        req=urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data=r.read()
            if data[:3]==b"ID3" or data[:2]==b"\xff\xfb":
                p=os.path.join(OUT, n.replace(" ","_")+".mp3")
                open(p,"wb").write(data)
                res[n]=[len(data), "OK"]
            else:
                res[n]=[len(data),"NOT_AUDIO"]
    except Exception as e:
        res[n]=[0, type(e).__name__]
for k,v in res.items(): print("%-26s %-12s %d" % (k, v[1], v[0]))
