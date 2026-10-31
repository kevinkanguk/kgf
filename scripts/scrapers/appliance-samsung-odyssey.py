import json, re, html, urllib.request, urllib.parse, os
BASE = "https://www.samsung.com"
EVENT = BASE + "/sec/event/2026-oled-benefit/"
MON = BASE + "/sec/event/samsung-monitor/"   # price cards (same Samsung display API)
SRC = "appliance-samsung-odyssey"
CACHE = "E:/090_ETC/kf/data/cache/html/" + SRC
OUT = "E:/090_ETC/kf/data/raw/catalog/appliance/%s.json" % SRC
os.makedirs(CACHE, exist_ok=True)

def fetch(url, name, ref=EVENT):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": ref}), timeout=40).read()
        open(f"{CACHE}/{name}", "wb").write(b)
    except Exception:
        try: b = open(f"{CACHE}/{name}", "rb").read()
        except Exception: b = None
    return b

def num(s):
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None
def attrs(tag): return dict(re.findall(r'([\w-]+)\s*=\s*"([^"]*)"', tag))
def img(blk):
    m = re.search(r'data-src="([^"]*images\.samsung\.com[^"]*)"', blk)
    if not m: return None
    u = m.group(1); return ("https:" + u) if u.startswith("//") else u

# 1. eligible models from the event notice
page = fetch(EVENT, "page.html").decode("utf-8", "replace")
i = page.find("LS55CG970NKXKR"); seg = page[i:i+2200]
seg = seg[:seg.find("</li>")]
pkgs = dict(re.findall(r'(LS\w+)\((LS\w+)\)', seg))
rest = re.sub(r'LS\w+\(LS\w+\)', '', seg)
models = list(dict.fromkeys(re.findall(r'LS[0-9A-Z]{8,}', rest)))
models += [p for p in pkgs]
models = list(dict.fromkeys(models))

# 2. price cards from Samsung monitor event (same API)
mp = fetch(MON, "monitor_page.html", MON).decode("utf-8", "replace")
cards = {}
def api(path, params, name):
    b = fetch(BASE + path + "?" + urllib.parse.urlencode(params), name + ".json", MON)
    return json.loads(b.decode("utf-8", "replace"))["html"] if b else ""
for c, en in re.findall(r'id="prodCard_prodList_(\d+)"\s*data-comp-no\s*=\s*"\d+"\s*data-comp-en-nm\s*=\s*"([^"]*)"', mp):
    h = api("/sec/cxhr/display/selectComponentGoodsList", dict(compNo=c, compEnNm=en, layoutNo=46, svmnAmtDispYn="Y", lastPrcText="혜택가", ctaMoveStyle=1, ctaWindowStyleClassNm="_self", broadcastId=""), c)
    for blk in re.split(r'(?=<div class="box-product-card")', h)[1:]:
        inner = attrs(re.search(r'<div class="inner"[^>]*>', blk, re.S).group(0))
        pt = attrs(re.search(r'<div[^>]*class="card-price"[^>]*>', blk, re.S).group(0))
        mg = re.search(r'goGoodsInfo\("([^"]*)",\s*"[^"]*",\s*"[^"]*",\s*"([^"]*)"', blk)
        cm = re.search(r'<input type="hidden" name="cardCompareInfo"[^>]*>', blk, re.S)
        ca = attrs(cm.group(0)) if cm else {}
        model = inner.get("data-mo-code") or (mg and mg.group(1))
        if not model or model in cards: continue
        cards[model] = dict(product=html.unescape(inner.get("data-goods-nm", "")), path=mg and mg.group(2),
            orig=num(pt.get("data-prd-price1")), member=num(pt.get("data-last-price")), benefit=num(pt.get("data-cp-apl-expt-price")),
            cpdc=num(inner.get("data-cp-dc-amt")), image=img(blk),
            rating=float(ca["data-review-grade"]) if ca.get("data-review-grade") else None, reviews=num(ca.get("data-review-count")))

# 3. build items
items, missing = [], []
for m in models:
    c = cards.get(m)
    if not c:
        for kind in ("gaming", "package"):
            u = f"{BASE}/sec/monitors/{kind}-{m.lower()}-d2c/{m}/"
            b = fetch(u, f"pd_{m}_{kind}.html")
            t = b.decode("utf-8", "replace") if b else ""
            pr = re.search(r'"sku":"%s".{0,400}?"price":(\d+)' % m, t, re.S)
            if pr and int(pr.group(1)) > 0:
                nm = re.search(r'"name":"([^"]*)","image":"([^"]*)"', t[t.find('"@type":"Product"'):])
                rt = re.search(r'"ratingValue":([\d.]+),"ratingCount":(\d+)', t)
                im = nm and nm.group(2)
                c = dict(product=html.unescape(nm.group(1)) if nm else m, path=f"/sec/monitors/{kind}-{m.lower()}-d2c/{m}/", orig=None,
                         member=int(pr.group(1)), benefit=None, cpdc=None, image=("https:" + im if im and im.startswith("//") else im),
                         rating=float(rt.group(1)) if rt else None, reviews=int(rt.group(2)) if rt else None)
                break
    if not c:
        missing.append(m); continue
    buy = BASE + c["path"] if (c["path"] or "").startswith("/") else EVENT
    sale = c["benefit"] or c["member"]
    cond = f"삼성닷컴 회원가 {c['member']:,}원" if c["member"] else ""
    if c["benefit"] and c["member"] and c["benefit"] != c["member"]:
        cond += f"; 쿠폰 적용 혜택가 {c['benefit']:,}원" + (f"(쿠폰할인 {c['cpdc']:,}원)" if c["cpdc"] else "")
    cond += "; 오디세이 OLED 구매 사은품 이벤트(네이버 등 대상, 2026-10-31까지 구매·11/30까지 신청) 대상 모델" + (f"; 패키지 구성 대표모델 {pkgs[m]}" if m in pkgs else "")
    pct = round((c["orig"] - sale) / c["orig"] * 100, 1) if c["orig"] and sale and c["orig"] > sale else None
    items.append(dict(item_id=f"{SRC}-{len(items)+1:04d}", category="appliance", source_id=SRC, unit="1대", vendor="삼성전자", channel="삼성닷컴",
        product=c["product"], model_code=m, buy_url=buy, image_url=c["image"], rating=c["rating"], review_count=c["reviews"],
        event_url=EVENT, claimed_original_price=c["orig"], sale_price=sale, claimed_discount_pct=pct, conditions=cond,
        price_60d_low=None, price_60d_typical=None, price_history_note=None, sources=[EVENT, buy],
        verify_status=None, verify_note=None, confidence=None))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(dict(category="appliance", source_id=SRC, collected_at="2026-10-31", items=items), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(models), len(items), "missing:", missing)
