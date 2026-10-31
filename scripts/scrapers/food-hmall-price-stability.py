"""Collect only the food tab of the officially linked Hmall KGF plan."""
import datetime,json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
SID='food-hmall-price-stability'
EVENT='https://www.hmall.com/md/dpa/searchSpexSectItem?sectId=2811083'
EVIDENCE='https://koreagrandfestival.kr/'
API='https://www.hmall.com/api/hf/dp/v1/sect-mng/'
def get(url,**kwargs):
 r=requests.get(url,timeout=30,**kwargs);r.raise_for_status();return r
def main():
 s=get(EVIDENCE).content.decode('utf8')
 if EVENT not in s.replace('&amp;','&'):raise RuntimeError('Official KGF link missing')
 d=get(API+'plansale-ancr-list',params={'sectId':2811083}).json()['respData']
 tabs=[x for x in d['ancrList'] if x.get('sectLbl')=='식품']
 if len(tabs)!=1 or tabs[0]['highSectId']!=2811083:raise RuntimeError('Food tab changed')
 tab=tabs[0]['sectId'];raw={};p=1
 while True:
  u=API+'plansale-ancr-paging';params={'sectId':tab,'page':p,'listSize':60,'searchMode':'true','searchYn':'Y','brndMallYn':'Y'}
  data=get(u,params=params).json()['respData'];rows=data.get('itemList') or []
  for o in rows:
   if o['slitmCd'] in raw:continue
   if o.get('sectId')!=tab:raise RuntimeError('Unexpected food tab result')
   raw[o['slitmCd']]=o
  if len(rows)<60:break
  p+=1
  if p>50:raise RuntimeError('Unexpected page count')
 items=[]
 for cd,o in raw.items():
  orig=o.get('sellPrc');sale=o.get('bbprc')
  if not sale or sale<=0 or not orig or orig<=sale:continue
  rc=o.get('reviewCnt');rt=o.get('itemEvalEvgScrg') if rc else None
  if rt is not None and not 0<=float(rt)<=5:raise RuntimeError('Unknown rating scale')
  img=o.get('itemBaseImgNm') or o.get('orglImgNm')
  image=f'https://image.hmall.com/static/{cd[7]}/{cd[6]}/{cd[4:6]}/{cd[2:4]}/{img}?RS=300x300' if img and len(cd)==10 else None
  items.append(dict(item_id=SID+'-'+str(len(items)+1).zfill(4),category='food',source_id=SID,vendor=o.get('venNm') or o.get('brndNm') or '현대Hmall',channel='현대Hmall 코그페 공식 링크 - 물가안정 프로젝트 식품',product=o['slitmNm'],model_code=None,unit=None,buy_url='https://www.hmall.com/pd/pda/itemPtc?slitmCd='+cd,image_url=image,rating=rt,review_count=rc,event_url=EVENT,kgf_evidence=EVIDENCE,claimed_original_price=orig,sale_price=sale,claimed_discount_pct=round((orig-sale)/orig*100,2),conditions='기획전 bbprc 쿠폰 적용가; 쿠폰 할인액 '+str(o.get('copnDcAmt'))+'원. 상세 조건 확인 필요.',sources=[EVIDENCE,EVENT,u+'?sectId='+str(tab)+'&page='+str(p)]))
 issues=['공식 코그페 홈페이지 직접 링크 확인. 전체몰 제외; 상위 기획전 2811083의 식품 탭 '+str(tab)+'만 전수 수집. 전체 원천 '+str(len(raw))+'건; 할인가 0/빈값/할인 없는 항목 제외.']
 if len(raw)>300:issues.append('추정치 5배 초과 후 범위 재확인: 공식 홈페이지 기획전 링크와 식품 하위 탭의 highSectId 일치 확인.')
 out=ROOT/'data/raw/catalog/food'/(SID+'.json');out.write_text(json.dumps(dict(category='food',source_id=SID,collected_at=datetime.datetime.now().astimezone().isoformat(),items=items,issues=issues),ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(SID,len(items),'raw',len(raw))
if __name__=='__main__':main()
