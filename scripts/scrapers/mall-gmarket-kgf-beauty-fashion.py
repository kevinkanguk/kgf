# -*- coding: utf-8 -*-
"""G마켓 코그페 뷰티/패션 기획전(exhib=280311, comp_27870414) 전 품목 수집. 실행: py -I 이 파일"""
import re, json, html, os, sys, time, datetime
from urllib.parse import unquote
import requests

SID = "mall-gmarket-kgf-beauty-fashion"
ROOT = "E:/090_ETC/kf"
CACHE = f"{ROOT}/data/cache/html/{SID}"
OUT = f"{ROOT}/data/raw/catalog/mall/{SID}.json"
EVENT = "https://rpp.gmarket.co.kr/?exhib=280311#comp_27870414"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
     "Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://rpp.gmarket.co.kr/?exhib=280311"}
os.makedirs(CACHE, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=H, timeout=60, **kw)
            r.raise_for_status()
            return r
        except Exception as e:
            print("retry", i, e, file=sys.stderr); time.sleep(2 + i * 2)
    raise RuntimeError(url)

pg = f"{CACHE}/page.html"
if not os.path.exists(pg) or os.path.getsize(pg) < 1_000_000:
    open(pg, "wb").write(get("https://rpp.gmarket.co.kr/?exhib=280311").content)
h = open(pg, encoding="utf-8").read()
a = h.find('id="comp_27870414"'); b = h.find('id="comp_27870415"', a)
seg = h[a:b]

tabs = []  # (cat_id, name)
for m in re.finditer(r'<button[^>]*value="inven_cat_(\d+)"[^>]*>([^<]*)</button>', seg):
    tabs.append((m.group(1), m.group(2).strip()))
# 더보기 버튼 파라미터
mores = {}
for m in re.finditer(r"getItemList\(this, (\d+),(\d+),(\d+),'([^']*)',(\w+), (\d+), (\d+), (\w+), (\d+), '([0-9a-f]+)', (\d+)\);\"[^>]*data-max-goods=\"(\d+)\" data-page-size=\"(\d+)\"", seg):
    mores[m.group(7)] = dict(inven_seq=m.group(1), view_type=m.group(2), comp_index=m.group(3), comp_name=m.group(4),
        is_pay=m.group(5), goods_expose_cnt=m.group(6), lclass=m.group(7), isnova=m.group(8), planid=m.group(9),
        uid=m.group(10), tab=m.group(11), maxg=int(m.group(12)), psize=int(m.group(13)))

def utparam(url):
    u = unquote(unquote(html.unescape(url)))
    d = {}
    for k in ("origin_price", "promotion_price", "coupon_price"):
        m = re.search(r'"%s":"?(\d+)' % k, u)
        d[k] = int(m.group(1)) if m else None
    return d

def to_int(x):
    return int(x) if x not in (None, "") else None

recs = {}  # goodscode -> rec
def add(code, name, img, url, op, pp, cp, shown_pct, tab):
    if code in recs:
        recs[code]["_tabs"].add(tab); return
    if img and img.startswith("//"): img = "https:" + img
    recs[code] = dict(code=code, name=name, img=img, url=url, op=op, pp=pp, cp=cp, pct=shown_pct, _tabs={tab})

# 1) 초기 HTML (탭별 첫 24개)
tab_ranges = []
for ci, (cid, tname) in enumerate(tabs):
    s = seg.find(f'id="inven_cat_{cid}"')
    e = seg.find(f'id="inven_cat_{tabs[ci+1][0]}"', s) if ci + 1 < len(tabs) else len(seg)
    part = seg[s:e]
    for li in re.split(r'<li class="elements_item', part)[1:]:
        mc = re.search(r'data-goods-no="(\d+)"', li)
        if not mc or 'class="title product-clk-spm-d"' not in li:
            continue
        code = mc.group(1)
        name = html.unescape(re.search(r'class="title product-clk-spm-d"[^>]*>([^<]*)</a>', li).group(1)).strip()
        img = re.search(r'data-original="([^"]+)"', li)
        img = html.unescape(img.group(1)) if img else None
        href = html.unescape(re.search(r'href="([^"]+)"', li).group(1))
        ut = utparam(href)
        op = re.search(r'<del class="num">([\d,]+)</del>', li)
        op = int(op.group(1).replace(",", "")) if op else ut["origin_price"]
        sell = re.search(r'<li class="selling">\s*<strong>([\d,]+)</strong>', li)
        sell = int(sell.group(1).replace(",", "")) if sell else None
        pct = re.search(r'<li class="discount">(\d+)<span>', li)
        pct = float(pct.group(1)) if pct else None
        add(code, name, img, f"https://item.gmarket.co.kr/Item?goodscode={code}", op, ut["promotion_price"], ut["coupon_price"] or sell, pct, tname)
        if sell is not None and recs[code]["cp"] is None: recs[code]["cp"] = sell
    print("html", tname, len([1 for r in recs.values() if tname in r["_tabs"]]), file=sys.stderr)

# 2) 더보기 API
for ci, (cid, tname) in enumerate(tabs):
    m = mores.get(cid)
    if not m: continue
    page = 2
    while (page - 1) * m["psize"] < m["maxg"]:
        p = dict(inven_seq=m["inven_seq"], page_no=page, page_size=m["psize"], view_type=m["view_type"],
                 comp_index=m["comp_index"], comp_name=m["comp_name"], is_pay_cnt_expose=m["is_pay"],
                 goods_expose_cnt=m["goods_expose_cnt"], inven_lclass_seq=m["lclass"], isnova=m["isnova"],
                 planid=m["planid"], comp_unique_id=m["uid"], moduleIdx=5, moduleIdxTotal=5, tabIndex=m["tab"],
                 lastListNo=(page - 1) * m["psize"] - 1)
        r = get("https://rpp.gmarket.co.kr/getInventoryItem", params=p)
        open(f"{CACHE}/more_{cid}_{page}.json", "wb").write(r.content)
        d = r.json()
        for it in d.get("inventoryList", []):
            code = str(it["goodsNo"])
            ut = utparam(it.get("landingUrl", ""))
            cai = it.get("couponAppliedPriceInfo") or {}
            cp = ut["coupon_price"] or cai.get("couponAppliedPrice")
            op = ut["origin_price"] or to_int(it.get("sellPrice"))
            pp = ut["promotion_price"] or to_int(it.get("discountPrice"))
            add(code, it.get("goodsName", "").strip(), it.get("goodsImageUrl"),
                f"https://item.gmarket.co.kr/Item?goodscode={code}", op, pp, cp, None, tname)
        page += 1
        time.sleep(0.5)

# 3) 출력
items = []
for n, r in enumerate(recs.values(), 1):
    op, pp, cp = r["op"], r["pp"], r["cp"]
    sale = cp if cp else pp
    cond = None
    if cp and pp and cp < pp:
        cond = "G마켓 쿠폰 적용가(기획전 쿠폰 등 조건 있음, 목록 표기가 기준). 쿠폰 미적용 판매가 %s원" % format(pp, ",")
    pct = r["pct"]
    if op and sale and op > 0 and sale < op:
        pct = round((op - sale) / op * 100, 1)
    elif op and sale: pct = 0.0
    items.append(dict(
        item_id=f"{SID}-{n:04d}", category="mall", source_id=SID, unit=None,
        vendor="G마켓 판매자(브랜드 미표기)", channel="G마켓 코그페 뷰티/패션 기획전 - " + "/".join(sorted(r["_tabs"])),
        product=r["name"], model_code=None, buy_url=r["url"], image_url=r["img"], rating=None, review_count=None,
        event_url=EVENT, claimed_original_price=op, sale_price=sale, claimed_discount_pct=pct, conditions=cond,
        price_60d_low=None, price_60d_typical=None, price_history_note=None, sources=[EVENT], 
        verify_status=None, verify_note=None, confidence=None))
out = dict(category="mall", source_id=SID, collected_at=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+09:00"), items=items)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("items", len(items), "expected", sum(m["maxg"] for m in mores.values()))
