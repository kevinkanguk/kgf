"""Enrich an existing official participant offer from its public card metadata.
Run: .python/python.exe -I scripts/scrapers/_kgf_official_offer_metadata.py <catalog.json>
"""
from html.parser import HTMLParser
from pathlib import Path
import json,sys
import requests
class Cards(HTMLParser):
 def __init__(self):super().__init__();self.vendor=None;self.images={}
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='li':self.vendor=d.get('data-name')
  if t=='img' and self.vendor and d.get('src'):self.images[self.vendor]=d['src']
 def handle_endtag(self,t):
  if t=='li':self.vendor=None
def main():
 path=Path(sys.argv[1]);data=json.loads(path.read_text(encoding='utf8'));event='https://koreagrandfestival.kr/sme'
 r=requests.get(event,timeout=30);r.raise_for_status();p=Cards();p.feed(r.content.decode('utf8'))
 for item in data['items']:
  if item['kgf_evidence']!=event:raise RuntimeError('Only official participant offers supported')
  if not item.get('image_url'):item['image_url']=p.images.get(item['vendor'])
 data.setdefault('issues',[]).append('대표 이미지는 공식 참여업체 카드 이미지. 상품 상세의 이미지·별점·리뷰수는 별도 미확인.')
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
