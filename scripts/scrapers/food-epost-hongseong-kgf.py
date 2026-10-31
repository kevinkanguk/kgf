"""Official KGF participant's complete advertised offer (one product).

Run from the repository: .venv/Scripts/python.exe -I scripts/scrapers/food-epost-hongseong-kgf.py
Only the named participant's explicit KGF offer is in scope, not its store catalog.
"""
import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re

import requests

ROOT = Path(__file__).resolve().parents[2]
SID = 'food-epost-hongseong-kgf'
EVENT = 'https://koreagrandfestival.kr/sme'
VENDOR = '홍성한우돈직판장'


class Offers(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.rows = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'li':
            self.active = a.get('data-name') == VENDOR
            if self.active:
                self.memo = a.get('data-memo', '')
        if self.active and tag == 'a' and a.get('data-online-url'):
            self.rows.append((self.memo, a['data-online-url']))

    def handle_endtag(self, tag):
        if tag == 'li':
            self.active = False


def main():
    r = requests.get(EVENT, timeout=30)
    r.raise_for_status()  # Do not retry or bypass 403/429.
    parser = Offers()
    parser.feed(r.content.decode('utf-8'))
    offers = set(parser.rows)  # Official site repeats cards in regional filters.
    if len(offers) != 1:
        raise RuntimeError('Participant offer changed; review scope before collecting')
    memo, buy = offers.pop()
    if '코그페' not in memo or '국내산 수제 돼지양념갈비' not in memo:
        raise RuntimeError('Explicit KGF product evidence missing')
    match = re.search(r'(\d[\d,]*)원\s*->\s*(\d[\d,]*)원', memo)
    if not match:
        raise RuntimeError('Explicit original/sale prices missing')
    original, sale = (int(v.replace(',', '')) for v in match.groups())
    if sale <= 0 or sale >= original:
        raise RuntimeError('Not a discounted priced product')
    item = dict(item_id=SID+'-0001', category='food', source_id=SID,
                vendor=VENDOR, channel='우체국쇼핑', product='국내산 수제 돼지양념갈비',
                unit='3kg', model_code=None, buy_url=buy, image_url=None,
                rating=None, review_count=None, event_url=EVENT, kgf_evidence=EVENT,
                claimed_original_price=original, sale_price=sale,
                claimed_discount_pct=15,
                conditions=memo+'; 공식 참여업체 신고 가격. 상품 상세의 현재 가격·배송 조건은 별도 확인 필요.',
                sources=[EVENT, buy])
    out = ROOT/'data/raw/catalog/food'/f'{SID}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(category='food', source_id=SID,
        collected_at=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
        items=[item], issues=['image/rating/review_count not provided in official offer']),
        ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('saved 1')


if __name__ == '__main__':
    main()
