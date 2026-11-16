
import urllib.request, ssl, json, sys
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def head(u, timeout=25):
    try:
        req=urllib.request.Request(u, headers=UA, method="GET")
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            data=r.read(2048)
            return "OK %s type=%s first=%r" % (r.status, r.headers.get("Content-Type"), data[:40])
    except Exception as e:
        return "FAIL %s: %s" % (type(e).__name__, e)
tests = [
 "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Carefree.mp3",
 "https://incompetech.com/music/royalty-free/mp3-royaltyfree/Life%20of%20Riley.mp3",
 "https://archive.org/advancedsearch.php?q=kevin+macleod&fl%5B%5D=identifier&fl%5B%5D=title&rows=5&page=1&output=json",
]
for t in tests:
    print(t)
    print("   ", head(t))
