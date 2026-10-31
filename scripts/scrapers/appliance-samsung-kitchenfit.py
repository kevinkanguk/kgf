import json, re, os, urllib.request
SRC = "appliance-samsung-kitchenfit"
URL = "https://www.samsung.com/sec/event/kitchenfiterior/"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/appliance/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True)
try:
    b = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=40).read()
    open(CACHE + "/page.html", "wb").write(b)
except Exception:
    b = open(CACHE + "/page.html", "rb").read()
p = b.decode("utf-8", "replace")
# This page is a benefit/gift event page (cohabit purchase benefit, SNS event, moving-gift event);
# it has no product cards (no prodCard/goGoodsInfo/price attrs), only model-code wildcards (RM***64*).
cards = len(re.findall(r"goGoodsInfo|prodCard_prodList|data-prd-price1", p))
items = []  # no priced products exist on this page; nothing is fabricated
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="appliance", source_id=SRC, collected_at="2026-10-31", items=items), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("product cards found:", cards, "items:", len(items))
