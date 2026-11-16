
import urllib.request, ssl
UA={"User-Agent":"Mozilla/5.0"}
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
for u in ["https://huggingface.co/api/models/Xenova/clip-vit-base-patch32",
          "https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2/package.json",
          "https://pypi.org/simple/onnxruntime/"]:
    try:
        req=urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            b=r.read(200)
            print("OK  ", r.status, u, b[:80])
    except Exception as e:
        print("FAIL", type(e).__name__, str(e)[:80], u)
