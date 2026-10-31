"""Extract merchant rows from public Enuri HTML without treating them as history."""
import html
import json
import re
import sys
from pathlib import Path
import requests

CACHE=Path(__file__).resolve().parents[2]/'data/cache/html/price_codex_test'

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    out=[]
    for model in ['81411922','116255872']:
        url='https://www.enuri.com/detail.jsp?modelno='+model
        r=requests.get(url,timeout=20)
        if r.status_code in (403,429):
            break
        s=r.text
        (CACHE/('enuri_'+model+'.html')).write_text(s,encoding='utf-8')
        rows=re.findall(r'<tr\b[^>]*>.*?</tr>',s,re.S)
        result=[]
        for row in rows:
            if 'showPrice=' not in row:
                continue
            row=re.sub(r'<img\b[^>]*alt="([^"]*)"[^>]*>',r' \1 ',row)
            text=html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',row)))
            links=[html.unescape(u) for u in re.findall(r'href="([^"]+)"',row)]
            result.append({'text':text,'links':links})
        out.append({'model':model,'url':url,'rows':result})
        print(model,json.dumps(result,ensure_ascii=False),flush=True)
    (CACHE/'enuri_merchants.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
