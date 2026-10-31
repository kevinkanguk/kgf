import requests, re, json, html, os, time
SID='auto-carnoon-gmc-oct'
BASE='https://www.carnoon.co.kr'
EVENT=BASE+'/newcar/discount/132'
CACHE='E:/090_ETC/kf/data/cache/html/'+SID
OUT='E:/090_ETC/kf/data/raw/catalog/auto/'+SID+'.json'
H={'User-Agent':'Mozilla/5.0'}
os.makedirs(CACHE,exist_ok=True); os.makedirs(os.path.dirname(OUT),exist_ok=True)
def get(url,name):
    p=f'{CACHE}/{name}'
    if os.path.exists(p): return open(p,encoding='utf-8').read()
    t=requests.get(url,headers=H,timeout=30).content.decode('utf-8')
    open(p,'w',encoding='utf-8').write(t); time.sleep(0.3); return t
def txt(s):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
page=get(EVENT,'discount_132.html')
blocks=page.split('<div class="model">')[1:]
items=[]
for b in blocks:
    title=txt(re.search(r'<div class="title">(.*?)</div>',b,re.S).group(1))
    vid=re.search(r'/newcar/vehicle/(\d+)',b).group(1)
    img=re.search(r'<div class="car"><img src="([^"]+)"',b)
    disc=b.split('id="discountNewcar"')[1] if 'id="discountNewcar"' in b else ''
    disc=disc.split('<div class="model">')[0]
    parts=[]
    total=0
    for li in re.findall(r'<li(?: class=\'term\')?>\s*(?:<div class="name">.*?)(?=<li>\s*<div class="name">|\Z)',disc,re.S):
        pass
    for li in re.split(r"(?=<li>\s*<div class=\"name\">|<li class='term'>)",disc)[1:]:
        name=txt(re.search(r"<div class=['\"]name['\"]>(.*?)</div>",li,re.S).group(1))
        vals=[]
        for v in re.findall(r"<li><span class=['\"]require['\"]>(.*?)</span>\s*(?:<span class=\"price\">(.*?)<span class='unit'>)?",li,re.S):
            req=txt(v[0]); pr=txt(v[1])
            vals.append((req+' '+pr+('원' if pr else '')).strip())
        note=re.search(r"<div class='text[^']*'>(.*?)</div>",li,re.S)
        s=name+': '+' / '.join(vals)
        if note: s+=' ['+txt(note.group(1))+']'
        parts.append(s)
    # unit: delivery term
    term=''
    m=re.search(r"예상납기[^<]*?</div><ul class='value'><li><span class='require'>(.*?)</span>",disc)
    if not m: m=re.search(r"<div class='name'>[^<]*</div><ul class='value'><li><span class='require'>(.*?)</span>",disc)
    pagev=get(f'{BASE}/newcar/vehicle/{vid}',f'vehicle_{vid}.html')
    pt=txt(pagev)
    pm=re.search(r'가격\s*([\d,]+)\s*~\s*([\d,]+)\s*만원',pt)
    cond='카눈 집계 2026년 10월 판매조건: '+' | '.join(parts)
    if pm: cond+=f' | 차량 가격대 {pm.group(1)}~{pm.group(2)}만원'
    items.append(dict(
        item_id=f'{SID}-{len(items)+1:04d}',category='auto',source_id=SID,unit=None,
        vendor='GMC',channel='카눈(판매조건 집계)',product=title,model_code=vid,
        buy_url=f'{BASE}/newcar/vehicle/{vid}',image_url=img.group(1) if img else None,
        rating=None,review_count=None,event_url=EVENT,
        claimed_original_price=None,sale_price=None,claimed_discount_pct=None,
        conditions=cond,sources=[EVENT,f'{BASE}/newcar/vehicle/{vid}']))
json.dump(dict(category='auto',source_id=SID,collected_at='2026-10-31',items=items),open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(len(items))
