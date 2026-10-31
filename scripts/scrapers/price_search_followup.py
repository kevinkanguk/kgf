"""Follow up cached batch searches with public Fallcent searches and merchant pages."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'data/cache/html/price_codex_test'

def main():
    rows = json.loads((CACHE / 'research.json').read_text(encoding='utf-8'))
    out = []
    blocked = set()
    for e in rows:
        url = 'https://fallcent.com/product/search/?' + urlencode({'keyword': e['item']['product']})
        if 'fallcent' in blocked:
            out.append({'item_id': e['item']['item_id'], 'url': url, 'status': 'blocked earlier'})
            continue
        try:
            r = requests.get(url, timeout=15)
            if r.status_code in (403,429):
                blocked.add('fallcent')
            text = re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>', '', r.text, flags=re.S|re.I)
            text = re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', text))
            out.append({'item_id':e['item']['item_id'], 'url':url, 'status':r.status_code, 'text':text})
        except requests.RequestException as exc:
            out.append({'item_id':e['item']['item_id'], 'url':url, 'status':type(exc).__name__})
        (CACHE/'followup.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
        print(e['item']['item_id'],out[-1]['status'],flush=True)

if __name__ == '__main__':
    main()
