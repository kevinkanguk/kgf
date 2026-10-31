"""카카오톡 예약하기 숙박세일페스타 소스 수집 시도.
booking.kakao.com 은 Next.js SSG 셸(스플래시만 포함)이며 숙소 목록은 앱/카카오톡 내 로그인 영역에서만 제공됨.
정적으로 얻을 수 있는 품목이 없어 items=[] 로 저장한다 (needs_browser/app)."""
import requests, json, datetime, pathlib
SID="travel_dutyfree-ota-kakao-booking-staysale"
root=pathlib.Path(__file__).resolve().parents[2]
cache=root/"data/cache/html"/SID; cache.mkdir(parents=True,exist_ok=True)
r=requests.get("https://booking.kakao.com/",headers={"User-Agent":"Mozilla/5.0"},timeout=20)
(cache/"home.html").write_text(r.text,encoding="utf8")
out=root/"data/raw/catalog/travel_dutyfree"/f"{SID}.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps({"category":"travel_dutyfree","source_id":SID,
 "collected_at":datetime.date.today().isoformat(),"items":[],
 "issues":["needs_browser: 숙소 목록/쿠폰 대상은 앱·카카오톡 내 JS 렌더링, 웹 셸에 품목 없음"]},ensure_ascii=False,indent=2),encoding="utf8")
