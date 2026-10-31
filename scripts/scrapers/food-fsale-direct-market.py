import requests,re,json,html,os,datetime
H={'User-Agent':'Mozilla/5.0'}
SID='food-fsale-direct-market'
CD='E:/090_ETC/kf/data/cache/html/'+SID+'/'
OUT='E:/090_ETC/kf/data/raw/catalog/food/'+SID+'.json'
BASE='https://www.fsale.kr/bbs/board.php?bo_table=directmarket'
os.makedirs(CD,exist_ok=True);os.makedirs(os.path.dirname(OUT),exist_ok=True)
items=[];p=1;last=1
while p<=last:
    u=BASE+('' if p==1 else '&page=%d'%p)
    r=requests.get(u,headers=H,timeout=30);r.encoding='utf8';t=r.text
    open(CD+'p%d.html'%p,'w',encoding='utf8').write(t)
    if p==1:
        last=max([int(x) for x in re.findall(r'page=(\d+)"',t)] or [1])
    for row in re.split(r'<td class="td_num2',t)[1:]:
        m=re.search(r'>\s*(\d+)\s*</td>',row);d=re.search(r'<span class="subj">(.*?)</span>(.*?)<div class="addr">(.*?)</div>',row,re.S)
        if not(m and d):print('skip',p,row[:80]);continue
        parts=[x.strip() for x in html.unescape(re.sub(r'<[^>]+>','',d.group(2))).split('|')]
        parts=[x for x in parts if x]+['','']
        items.append((int(m.group(1)),html.unescape(d.group(1)).strip(),parts[0],parts[1],html.unescape(d.group(3)).strip(),u))
    p+=1
items.sort(key=lambda x:-x[0])
out=[]
for k,(no,date,sido,sigun,addr,u) in enumerate(items,1):
    out.append({"item_id":"%s-%04d"%(SID,k),"category":"food","source_id":SID,"unit":None,
      "vendor":"%s %s"%(sido,sigun),"channel":"농산물 직거래장터(직거래 장터)",
      "product":"직거래장터 %s %s %s (%s)"%(date,sido,sigun,addr),"model_code":None,
      "buy_url":BASE,"image_url":None,"rating":None,"review_count":None,"event_url":BASE,
      "claimed_original_price":None,"sale_price":None,"claimed_discount_pct":None,
      "conditions":"오프라인 행사. 일자 %s, 장소 %s. 게시글 번호 %d"%(date,addr,no),
      "sources":[u]})
json.dump({"category":"food","source_id":SID,"collected_at":"2026-10-31","items":out},open(OUT,'w',encoding='utf8'),ensure_ascii=False,indent=2)
print(len(out))
