"""Collect general search snippets for exact brand/spec merchant discovery."""
import json
import re
from pathlib import Path
import requests

CACHE=Path(__file__).resolve().parents[2]/'data/cache/html/price_codex_test'

if __name__=='__main__':
    out=[]
    for e in json.loads((CACHE/'research.json').read_text(encoding='utf-8')):
        q=e['item']['product']+' 가격'
        try:
            r=requests.get('https://search.naver.com/search.naver',params={'query':q},timeout=12)
            s=re.sub(r'<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>',' ',r.text,flags=re.S|re.I)
            s=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',s))
            out.append({'item_id':e['item']['item_id'],'url':r.url,'status':r.status_code,'text':s})
            if r.status_code in (403,429):
                break
        except requests.RequestException as exc:
            out.append({'item_id':e['item']['item_id'],'status':type(exc).__name__})
        (CACHE/'naver.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    (CACHE/'naver.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
