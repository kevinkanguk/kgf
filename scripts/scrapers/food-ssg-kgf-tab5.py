"""Resume a previously registered KGF source. Run with .python/python.exe -I."""
import datetime,json,re
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
SID='food-ssg-kgf-tab5'
CAT=SID.split('-')[0]
H={'User-Agent':'Mozilla/5.0','Referer':'https://www.ssg.com/','Origin':'https://www.ssg.com'}
def get(url,**kw):
 r=requests.get(url,timeout=30,**kw);r.raise_for_status();return r
def n(v):
 try:return float(v) if v not in ('',None,'null') else None
 except (ValueError,TypeError):return None
def main():
 issues=[];items=[];seen=set()
 if 'ssg' in SID:
  event='https://www.ssg.com/plan/planShop.ssg?dispCmptId=6000465146'
  html=get(event).content.decode('utf8')
  if 'KOREA GRAND FESTIVAL' not in html:raise RuntimeError('KGF evidence missing')
  themes=['7000886052','7000886054','7000886063','7000886055','7000949389','7000886051','7000886053']
  theme=themes[int(SID[-1])-1]
  if theme not in html:raise RuntimeError('Theme no longer in KGF page')
  api='https://frontapi.ssg.com/dp/api/v1/planshop/store/item/plain'
  p=1
  while True:
   body={'common':{'aplVer':'','osCd':'','mobilAppNo':'99','dispDvicDivCd':'10','viewSiteNo':'6005'},'params':{'dispCmptId':'6000465146','inflowSiteNo':'6005','themeId':theme,'page':p,'pageSize':30}}
   r=requests.post(api,json=body,headers=H,timeout=30);r.raise_for_status();d=r.json()['data'];rows=d.get('itemList') or []
   if d.get('themeId')!=theme or d.get('dispCmptId')!='6000465146':raise RuntimeError('Unexpected scope')
   for o in rows:
    key=o['itemId']
    if key in seen:continue
    seen.add(key);sale=n(o.get('displayPrc'));orig=n(o.get('strikeOutPrc'))
    if not sale or sale<=0:continue
    rate=n(o.get('priceInfo',{}).get('raw',{}).get('discountRate'))
    # No discount is not a KGF price offer.
    if not ((orig and orig>sale) or (rate and rate>0)):continue
    rt=n(o.get('recompPoint'))
    if rt is not None and not 0<=rt<=5:raise RuntimeError('Unknown rating scale')
    items.append(dict(vendor=o.get('brandNm') or 'SSG 판매자',channel='SSG 코그페 소상공인 브랜드대전',product=o['itemNm'],model_code=o.get('modelInfo') or None,unit=None,buy_url=o['itemLnkd'],image_url=o.get('itemImgUrl') or None,rating=rt,review_count=n(o.get('recomRegCnt')),claimed_original_price=orig,sale_price=sale,claimed_discount_pct=rate if rate else round((orig-sale)/orig*100,2),conditions=o.get('priceInfo',{}).get('summary',{}).get('cpnTxt') or None,sources=[event,api+'?themeId='+theme+'&page='+str(p)]))
   if len(seen)>200 and not issues:issues.append('추정치 5배 초과 재확인: 코그페 배너가 있는 dispCmptId=6000465146의 해당 themeId만 수집; API 응답의 dispCmptId와 themeId 일치 확인')
   if not d.get('hasNext'):break
   if not rows or p>=100:raise RuntimeError('Incomplete pagination')
   p+=1
 else:
  event='https://www.skstoa.com/plan/event/detail/2026103519';api='https://www.skstoa.com/plan/planDetail/more'
  html=get(event).content.decode('utf8')
  if '코리아 그랜드페스티벌' not in html:raise RuntimeError('KGF evidence missing')
  tabs=re.findall(r"changePlanShop\('([0-9]+)', '30', '([0-9]+)', '4'\)",html)
  expected=dict(tabs)
  groups=['01'] if CAT=='food' else ['01','02','04','05','03']
  raw={}
  for gb in groups:
   count=int(expected[gb]);rows=[];p=1
   while True:
    params={'planCode':'2026103519','rangeType':'30','orderType':'4','planGoodsGb':gb,'currentPage':p,'rowsPerPage':60,'displayDate':''}
    batch=get(api,params=params,headers={'Referer':event,'X-Requested-With':'XMLHttpRequest'}).json()['planSeriesGoods']
    if not batch:break
    for o in batch:
     if o['planCode']!='2026103519' or o['planGoodsGb']!=gb or '코리아' not in o['planName']:raise RuntimeError('Unexpected KGF tab scope')
     raw[o['goodsCode']]=o
    rows+=batch
    if len(batch)<60:break
    p+=1
    if p>20:raise RuntimeError('Unexpected pagination')
   if len(rows)>count*5:raise RuntimeError('Scope exceeds published tab count fivefold')
   issues.append('tab '+gb+': page count '+str(count)+', API rows '+str(len(rows))+'; planCode/planGoodsGb/planName 확인')
  if CAT=='food':issues.append('추정 30개 초과 범위 재확인: 코그페 식품 탭(01)과 API 개별 상품의 planName 및 planGoodsGb=01 일치')
  for o in raw.values():
   orig=n(o.get('salePrice'));sale=n(o.get('bestPrice'));m=re.search(r'정상가\s*([\d,]+)원',o['goodsName'])
   if m and orig and (not sale or sale>=orig):sale=orig;orig=int(m.group(1).replace(',',''))
   if not sale or sale<=0 or not orig or orig<=sale:continue
   rt=n(o.get('argCommentSumDouble')) if o.get('commentCnt') else None
   if rt is not None and not 0<=rt<=5:raise RuntimeError('Unknown rating scale')
   image='https://imagecdn.skstoa.com'+o['imageUrl']+o['imageH'] if o.get('imageUrl') and o.get('imageH') else None
   items.append(dict(vendor=o.get('brandName') or 'SK스토아',channel='SK스토아 코리아 그랜드페스티벌',product=o['goodsName'],model_code=None,unit=None,buy_url='https://www.skstoa.com/display/goods/'+o['goodsCode'],image_url=image,rating=rt,review_count=o.get('commentCnt'),claimed_original_price=orig,sale_price=sale,claimed_discount_pct=n(o.get('couponRate')) or round((orig-sale)/orig*100,2),conditions='기획전 bestPrice(쿠폰/즉시할인 포함 가능). 상세 조건 확인 필요.',sources=[event,api+'?planCode=2026103519&planGoodsGb='+o['planGoodsGb']]))
 for i,o in enumerate(items,1):o.update(item_id=SID+'-'+str(i).zfill(4),category=CAT,source_id=SID,event_url=event,kgf_evidence=event)
 out=ROOT/'data/raw/catalog'/CAT/(SID+'.json');out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(category=CAT,source_id=SID,collected_at=datetime.datetime.now().astimezone().isoformat(),items=items,issues=issues),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(SID,len(items))
if __name__=='__main__':main()
