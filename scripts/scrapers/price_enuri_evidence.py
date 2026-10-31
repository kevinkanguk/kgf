"""Inspect public Enuri price-chart endpoints and collect matched catalog pages."""
import concurrent.futures
import json
import re
import sys
from pathlib import Path
import requests

CACHE = Path(__file__).resolve().parents[2] / 'data/cache/html/price_codex_test'

def get(u):
    r = requests.get(u, timeout=20)
    return u, r.status_code, r.text

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    html = (CACHE/'enuri_gold.html').read_text(encoding='utf-8')
    urls = list(dict.fromkeys(re.findall(r'<script[^>]+src="([^"]+)',html)))
    urls = ['https://www.enuri.com'+u if u.startswith('/') else u for u in urls if '_next' in u]
    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        for n,(url,status,body) in enumerate(pool.map(get,urls)):
            (CACHE/f'enuri_js_{n}.txt').write_text(body,encoding='utf-8')
            matches = re.findall(r'.{0,100}(?:priceHistory|price-history|priceTrend|price-trend|price/chart|priceChart|priceGraph|price-graph).{0,220}',body)
            if matches:
                print(url,status,'\n'+'\n'.join(matches[:15]),flush=True)
