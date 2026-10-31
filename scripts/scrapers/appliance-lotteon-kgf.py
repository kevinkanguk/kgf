"""Review the registered appliance source against the current official plan tabs."""
import datetime,json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[2]
SID='appliance-lotteon-kgf'
EVENT='https://www.lotteon.com/display/planV2/planDetail/112088'
API='https://pbf.lotteon.com/display/v2/plan/seltPlanSctnListV2?mallNo=1&spdpNo=112088'
def main():
 r=requests.get('https://koreagrandfestival.kr/',timeout=30);r.raise_for_status()
 if EVENT not in r.content.decode('utf8'):raise RuntimeError('Official KGF plan link missing')
 r=requests.get(API,timeout=30);r.raise_for_status();tabs=r.json()['data']['sctnDetail']
 names=[x['sctnNm'] for x in tabs]
 # Do not pull unrelated living/general catalog products into appliances.
 if any('가전' in x or '디지털' in x for x in names):raise RuntimeError('Appliance tab appeared; implement complete pagination')
 issue='scope_unconfirmed: 공식 링크 기획전의 현재 탭은 '+', '.join(names)+'. 가전/디지털 전용 탭이 없어 가전 범위를 확인할 수 없음. 리빙 전체를 가전으로 추정 수집하지 않고 보류.'
 out=ROOT/'data/raw/catalog/appliance'/(SID+'.json')
 out.write_text(json.dumps(dict(category='appliance',source_id=SID,collected_at=datetime.datetime.now().astimezone().isoformat(),items=[],issues=[issue],event_url=EVENT,evidence_api=API),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(SID,'0; scope_unconfirmed')
if __name__=='__main__':main()
