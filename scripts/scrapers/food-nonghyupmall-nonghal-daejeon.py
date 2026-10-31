import re, json, html, os, datetime, requests
SID = "food-nonghyupmall-nonghal-daejeon"
BASE = "E:/090_ETC/kf"
EVT = "https://www.nonghyupmall.com/BC1B010R/evtDetail.nh?evtNo=EV20260070"
PLAN = "https://www.nonghyupmall.com/BC19030R/exhPlanDetailList.nh?crnC=004949&chanC=1101&mediaD=00&mbT=00&ctgrStp="
cache = f"{BASE}/data/cache/html/{SID}/plan.html"
if os.path.exists(cache):
    t = open(cache, encoding="utf-8", errors="replace").read()
else:
    r = requests.get(PLAN, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.encoding = "utf-8"; t = r.text
    open(cache, "w", encoding="utf-8").write(t)
tabs = [(m.group(1), html.unescape(m.group(2)).strip()) for m in re.finditer(r'<a href="#(\d+)" class="tab-link[^>]*>([^<]*)</a>', t)]
tabname = dict(tabs)
starts = [(m.start(), m.group(1)) for m in re.finditer(r'<div id="(\d+)" class="tab-cont', t)]
items, seen = [], set()
for k, (s, tid) in enumerate(starts):
    e = starts[k+1][0] if k+1 < len(starts) else len(t)
    seg = t[s:e]
    for li in re.split(r'<li class="prd-list-item[^"]*">', seg)[1:]:
        w = re.search(r'data-wrs-c="(\d+)"', li)
        if not w or w.group(1) in seen: continue
        seen.add(w.group(1))
        title = re.search(r'<p class="title">\s*(.*?)</p>', li, re.S)
        price = re.search(r'<strong class="price">\s*([\d,]+)', li)
        orig = re.search(r'<(?:del|s|span)[^>]*class="[^"]*(?:ori|before|through|cancel)[^"]*"[^>]*>\s*([\d,]+)', li)
        pct = None
        bullets = [html.unescape(b).strip() for b in re.findall(r"<span class=['\"]?txt-bullet[^>]*>(.*?)</span>", li, re.S)]
        alt = re.search(r'class="prd-img".*?<img src="[^"]*" alt="([^"]*)"', li, re.S)
        p = html.unescape(alt.group(1)).strip() if alt and alt.group(1).strip() else (html.unescape(title.group(1)).strip() if title else "")
        um = re.search(r'(\d+(?:\.\d+)?\s?(?:kg|g|ml|mL|L|입|개|팩|봉|포|박스|세트))', p)
        items.append({
            "item_id": f"{SID}-{len(items)+1:04d}", "category": "food", "source_id": SID,
            "unit": um.group(1) if um else None, "vendor": "농협몰", "channel": "농협몰 농할대전(대전환 농할대전)",
            "product": p, "model_code": w.group(1),
            "buy_url": f"https://www.nonghyupmall.com/BC14010R/viewDetailPage.nh?wrsC={w.group(1)}&chanC=1101",
            "event_url": EVT,
            "claimed_original_price": int(orig.group(1).replace(",", "")) if orig else None,
            "sale_price": int(price.group(1).replace(",", "")) if price else None,
            "claimed_discount_pct": None,
            "conditions": f"기획전 탭: {tabname.get(tid, tid)}" + (f"; 표기: {', '.join(bullets)}" if bullets else ""),
            "sources": [PLAN, EVT],
        })
out = {"category": "food", "source_id": SID, "collected_at": "2026-10-31", "items": items}
os.makedirs(f"{BASE}/data/raw/catalog/food", exist_ok=True)
json.dump(out, open(f"{BASE}/data/raw/catalog/food/{SID}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(items), sum(1 for i in items if i["sale_price"] is None), sum(1 for i in items if i["claimed_original_price"]), sum(1 for i in items if i["claimed_discount_pct"]))
