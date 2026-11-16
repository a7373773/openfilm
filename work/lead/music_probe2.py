
import urllib.request, ssl, os
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
names = ["Carefree","Life of Riley","Wallpaper","Cipher","Deliberate Thought","Ascending the Vale",
         "Enchanted Valley","Silver Blue Light","Floating Cities","Whispering Stream","Serenity",
         "Dreamy Flashback","Airport Lounge","Sincerely","Easy Lemon","Achaidh Cheide","Montauk Point",
         "Frost Waltz","Open Sea","Chill Wave","Peaceful","Wistful Harp","Bittersweet","Gymnopedie No 1"]
for n in names:
    u="https://incompetech.com/music/royalty-free/mp3-royaltyfree/"+urllib.parse.quote(n)+".mp3"
    try:
        req=urllib.request.Request(u, headers=dict(UA, Range="bytes=0-1023"))
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            d=r.read(1024)
            cl=r.headers.get("Content-Range") or r.headers.get("Content-Length")
        ok = d[:3]==b"ID3" or (len(d)>1 and d[0]==0xFF)
        print("%-22s %s %s %r" % (n, "OK " if ok else "BAD", cl, d[:4]))
    except Exception as e:
        print("%-22s FAIL %s" % (n, type(e).__name__))
