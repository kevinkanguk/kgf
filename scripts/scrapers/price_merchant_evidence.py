"""Fetch identified independent merchant pages; retain text evidence for review."""
import concurrent.futures
import json
import re
from pathlib import Path
import requests

CACHE = Path(__file__).resolve().parents[2] / 'data/cache/html/price_codex_test'
URLS = [
 'https://m.rokkiss.co.kr/product/list_thumb.html?cate_no=101',
 'https://www.11st.co.kr/products/5378944125',
 'https://www.hwahae.co.kr/goods/록키스-리쥬버네이팅-핑크-오일-55ml/64697',
 'https://www.enuri.com/detail.jsp?modelno=116255872',
 'https://www.enuri.com/detail.jsp?modelno=102837937',
 'https://www.ssg.com/item/itemView.ssg?itemId=1000462726887',
 'https://www.rokkiss.com/product/list.html?cate_no=62&page=1',
]

def get(url):
    try:
        r=requests.get(url,timeout=20)
        text=re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>',' ',r.text,flags=re.S|re.I)
        text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',text))
        return {'url':url,'status':r.status_code,'text':text}
    except requests.RequestException as exc:
        return {'url':url,'status':type(exc).__name__}

if __name__ == '__main__':
    # Different sites can be collected concurrently; requests to Enuri remain sequential.
    out=[]
    blocked=set()
    for u in URLS:
        host=requests.utils.urlparse(u).netloc
        if host in blocked:
            continue
        out.append(get(u))
        if out[-1]['status'] in (403,429):
            blocked.add(host)
        (CACHE/'merchants.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
