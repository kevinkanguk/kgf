import requests,re,json,html,os,sys
H={'User-Agent':'Mozilla/5.0'}
CD='E:/090_ETC/kf/data/cache/html/food-emart-nonghal/'
def get(u,n):
    r=requests.get(u,headers=H,timeout=30);r.encoding='utf8'
    open(CD+n,'w',encoding='utf8').write(r.text);return r.text
def pages(t):
    out=[]
    for m in re.finditer(r'<li><img class="d-cont-img"[^>]*data-src="([^"]+)" alt="([^"]*)"><div class="hide">(.*?)</div></li>',t,re.S):
        out.append((m.group(1),html.unescape(m.group(2)),html.unescape(m.group(3))))
    return out
if __name__=='__main__' and len(sys.argv)==1:
    for d,u in [('d4','https://store.emart.com/news/leaflet.do?division=4&seq=23239'),('d2','https://store.emart.com/news/leaflet.do?division=2'),('d3','https://store.emart.com/news/leaflet.do?division=3')]:
        t=get(u,d+'.html');p=pages(t);print(d,len(p))
        with open(CD+d+'_pages.txt','w',encoding='utf8') as f:
            for i,(img,alt,tx) in enumerate(p):f.write(f'#### {i} {img} {alt}\n{tx}\n')

# ---- parse (재실행: py -I scripts/scrapers/food-emart-nonghal.py parse) ----
LEAF='https://store.emart.com/news/leaflet.do?division=4&seq=23239'
EVENT='https://store.emart.com/news/event/notice_event_view.do?master_cd=32468'
BRANDS=['농심','오뚜기','양반','풀무원','제스프리','삼립','스타벅스','CJ','종가','명랑','한성','샘표','서울우유','파스퇴르','카누','남양','맥심','하겐다즈','동원','사조','자연주의','미미네','비비드키친','다향','쿠쿠']
NONFOOD=re.compile(r'주방세제|물걸레|세탁세제|물티슈|포터블 스크린|휘슬러|스타우브|기저귀|^<')
NUM=r'[\d,]+(?:/[\d,]+)*'
PERIOD=re.compile(r'행사기간 : (.*?)(?=\s*(?:\d[\d,]*(?:/[\d,]+)*(?:->|원|\s*1\+1|\s*2\+1)|신세계|행사카드|1개 구매|2개|\d개 |삼성포인트|$))')
def i(s):return int(s.replace(',',''))
def parse_line(line):
    line=line.strip().strip('"')
    if '행사기간' not in line:
        m=re.search(r'\s('+NUM+r')원\s*(.*)$',line)  # 기획상품: 가격만
        if not m:return None
        name=line[:m.start()]; rest=line[m.start():]; period=None
    else:
        name,rest=line.split('행사기간',1); period=None
        m=re.match(r'\s*:\s*(\d+\.\d+\([^)]\)\s*[-~]\s*(?:\d+\.\d+\([^)]\)|소진\s?시\s?까지)(?:,\s*[^\d\s]+\s*[^\d\s]*!)?)\s*(.*)$',rest)
        if m:period=m.group(1);rest=m.group(2)
    return name.strip(),period,rest.strip()
def build():
    t=open(CD+'d4.html',encoding='utf8').read();items=[]
    for idx,(img,alt,tx) in enumerate(pages(t)):
        if idx not in (1,2,3,5,6,7,8):continue
        for ln in tx.split('\n'):
            ln=ln.strip()
            if not ln or ln.startswith('[') or ln.startswith('※') or '대한민국 시그니처 세일' in ln[:40] and ln.startswith('[') :continue
            if NONFOOD.search(ln):continue
            if idx==8 and not re.search(r'남양 아이엠마더|뉴케어|상하목장',ln):continue
            if idx==1 and re.match(r'잇섭',ln):continue
            p=parse_line(ln)
            if not p:
                p=(ln.split('행사기간')[0].strip(),None,ln)
            name,period,rest=p
            name=re.sub(r'\s*대한민국 시그니처 세일 대한민국 쓱데이','',name).strip()
            rest=re.sub(r'^[,;]\s*','',rest)
            if not name:continue
            orig=sale=None
            m=re.search(r'('+NUM+r')원?\s*->\s*('+NUM+r')원',rest)
            if m:
                a,b=m.group(1),m.group(2)
                if '/' not in a and '/' not in b:orig,sale=i(a),i(b)
            else:
                m=re.match(r'('+NUM+r')원',rest)
                if m and '/' not in m.group(1):sale=i(m.group(1))
            pct=None
            if orig and sale and orig>0:pct=round((1-sale/orig)*100,1)
            else:
                m=re.search(r'(\d+)% 할인',rest)
                if m and orig is None and sale is None:pct=float(m.group(1))
            um=re.findall(r'\(([^()]*(?:\d+\s*(?:kg|g|ml|L|입|구|개|P|봉|팩|미|인분|종|롤|매|cm)|약\s*\d)[^()]*)\)',name)
            unit=um[0] if um else None
            vendor=next((b for b in BRANDS if name.startswith(b)),'이마트')
            cond=((('행사기간 '+period+'; ') if period else '')+rest).strip() or None
            if cond and cond.endswith(';'):cond=cond[:-1]
            items.append(dict(category='food',source_id='food-emart-nonghal',unit=unit,vendor=vendor,channel='이마트 쓱데이(대한민국 시그니처 세일, 전단 %d면)'%idx,
                product=name,model_code=None,buy_url=LEAF,image_url=img,rating=None,review_count=None,event_url=EVENT,
                claimed_original_price=orig,sale_price=sale,claimed_discount_pct=pct,conditions=cond,sources=[LEAF,EVENT]))
    for n,it in enumerate(items,1):
        it['item_id']='food-emart-nonghal-%04d'%n
    items=[{**{'item_id':it['item_id']},**{k:v for k,v in it.items() if k!='item_id'}} for it in items]
    import datetime
    out=dict(category='food',source_id='food-emart-nonghal',collected_at='2026-10-31',items=items)
    os.makedirs('E:/090_ETC/kf/data/raw/catalog/food',exist_ok=True)
    json.dump(out,open('E:/090_ETC/kf/data/raw/catalog/food/food-emart-nonghal.json','w',encoding='utf8'),ensure_ascii=False,indent=2)
    return items
if len(sys.argv)>1 and sys.argv[1]=='parse':
    it=build();print(len(it))
