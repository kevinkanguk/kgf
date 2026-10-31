"""Collect price research evidence for the 20 highest-discount unresearched items.

Evidence only: never infer a historical price from a current sale or list price.
Run with .python/python.exe -I scripts/scrapers/price_search_batch.py
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_report

CACHE = ROOT / 'data/cache/html/price_codex_test'
HEADERS = {'User-Agent': 'Mozilla/5.0'}


def collect():
    todo = [i for i in build_report.load() if i.get('price_60d_low') is None
            and i.get('price_60d_typical') is None and not i.get('price_history_note')
            and not (i['category'] == 'appliance' and i.get('model_code'))]
    todo.sort(key=lambda i: -(i.get('shown_discount_pct') or 0))
    todo = todo[:20]
    CACHE.mkdir(parents=True, exist_ok=True)
    blocked = set()
    evidence = []

    def fetch(url):
        host = urlsplit(url).netloc
        if host in blocked:
            return {'url': url, 'status': 'skipped: site blocked earlier'}
        key = hashlib.sha256(url.encode()).hexdigest()[:20]
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code in (403, 429):
                blocked.add(host)
            r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower() == 'iso-8859-1' else r.encoding
            (CACHE / (key + '.html')).write_text(r.text, encoding='utf-8')
            text = re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>', ' ', r.text, flags=re.S|re.I)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return {'url': url, 'final_url': r.url, 'status': r.status_code, 'cache': key + '.html', 'text': text[:45000]}
        except requests.RequestException as exc:
            return {'url': url, 'status': type(exc).__name__, 'error': str(exc)}

    # Site order is deliberate; after a block no later request is made to that host.
    for it in todo:
        q = it['product']  # Preserve brand names in square brackets and pack counts.
        urls = [
            'https://search.danawa.com/dsearch.php?' + urlencode({'query': q}),
            'https://www.enuri.com/search.jsp?' + urlencode({'keyword': q}),
            'https://fallcent.com/product/search/?' + urlencode({'keyword': q}),
            it['buy_url'],
            'https://search.naver.com/search.naver?' + urlencode({'query': q + ' 가격'}),
        ]
        results = [fetch(u) for u in urls]
        evidence.append({'item': it, 'results': results})
        (CACHE / 'research.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        print(it['item_id'], [(urlsplit(r['url']).netloc, r['status']) for r in results], flush=True)
    return evidence


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    collect()
