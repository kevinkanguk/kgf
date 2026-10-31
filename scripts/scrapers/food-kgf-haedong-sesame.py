"""Collect the complete named participant offer, not its full shop catalog."""
import datetime,json,re
from html.parser import HTMLParser
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
SID,VENDOR,PRODUCT,UNIT=('food-kgf-haedong-sesame', '해동제유소', '국내산 참기름', '350ml')
EVENT='https://koreagrandfestival.kr/sme'
class Offers(HTMLParser):
 def __init__(self):super().__init__();self.active=False;self.rows=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='li':
   self.active=a.get('data-name')==VENDOR
   if self.active:self.row={'memo':a['data-memo'],'address':a.get('data-addr'),'buy':None,'image':None};self.rows.append(self.row)
  if self.active and tag=='a' and a.get('data-online-url'):self.row['buy']=a['data-online-url']
  if self.active and tag=='img' and a.get('src'):self.row['image']=a['src']
 def handle_endtag(self,tag):
  if tag=='li':self.active=False
def main():
 r=requests.get(EVENT,timeout=30);r.raise_for_status();s=r.content.decode('utf8')
 if '코리아 그랜드 페스티벌' not in s:raise RuntimeError('KGF page evidence missing')
 p=Offers();p.feed(s)
 if not p.rows or len({x['memo'] for x in p.rows})!=1:raise RuntimeError('Participant scope changed')
 o=p.rows[0];memo=o['memo'];prices=re.findall(r'(\d[\d,]*)원',memo)
 if len(prices)<2:raise RuntimeError('Two explicit prices required')
 orig,sale=[int(v.replace(',','')) for v in prices[:2]]
 if not 0<sale<orig:raise RuntimeError('No discounted offer')
 pct=re.search(r'(\d+(?:\.\d+)?)%[ ]*할인',memo)
 issues=['공식 참여업체 카드에 공개된 전체 혜택 1종만 수집. 대표 이미지는 공식 업체 카드 이미지. 별점·리뷰수 미제공.']
 conditions=memo
 if o['address']:conditions+='; 오프라인 매장: '+o['address']
 if VENDOR=='대관령벌나무농장':conditions+='; 공식 표기 할인율 10%는 공개 가격으로 계산한 비율과 다름.'
 item=dict(item_id=SID+'-0001',category='food',source_id=SID,vendor=VENDOR,channel='코그페 공식 참여업체',product=PRODUCT,model_code=None,unit=UNIT,buy_url=o['buy'],image_url=o['image'],rating=None,review_count=None,event_url=EVENT,kgf_evidence=EVENT,claimed_original_price=orig,sale_price=sale,claimed_discount_pct=float(pct[1]) if pct else None,conditions=conditions,sources=[EVENT]+([o['buy']] if o['buy'] else []))
 out=ROOT/'data/raw/catalog/food'/(SID+'.json');out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(dict(category='food',source_id=SID,collected_at=datetime.datetime.now().astimezone().isoformat(),items=[item],issues=issues),ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(SID,1)
if __name__=='__main__':main()
