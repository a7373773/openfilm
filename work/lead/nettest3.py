
import urllib.request, ssl
UA={"User-Agent":"Mozilla/5.0"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
tests = [
 "https://hf-mirror.com/api/models/Xenova/clip-vit-base-patch32",
 "https://www.modelscope.cn/api/v1/models",
 "https://github.com",
 "https://raw.githubusercontent.com/xenova/transformers.js/main/package.json",
 "https://cdn.jsdelivr.net/gh/xenova/transformers.js/main/package.json",
 "https://registry.npmjs.org/@xenova%2Ftransformers",
 "https://hf-mirror.com/Xenova/clip-vit-base-patch32/resolve/main/config.json",
]
for u in tests:
    try:
        req=urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            b=r.read(120)
            print("OK  ", r.status, u, b[:60])
    except Exception as e:
        print("FAIL", type(e).__name__, str(e)[:60], u)
