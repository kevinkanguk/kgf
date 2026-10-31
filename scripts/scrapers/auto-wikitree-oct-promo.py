# -*- coding: utf-8 -*-
"""Wikitree article 989061 (domestic carmakers' Oct promotions). Article text is prose, so
model-level promo rows are transcribed from the cached article; prices are null (not stated)."""
import json, os, re, requests
ROOT = r"E:/090_ETC/kf"
SID = "auto-wikitree-oct-promo"; URL = "https://www.wikitree.co.kr/articles/989061"
CACHE = f"{ROOT}/data/cache/html/{SID}/article.html"
OUT = f"{ROOT}/data/raw/catalog/auto/{SID}.json"
if not os.path.exists(CACHE):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30); r.encoding = "utf8"
    open(CACHE, "w", encoding="utf8").write(r.text)
# (vendor, product, benefit_text)
R = []
def a(v, p, c): R.append((v, p, c))
for p in ["아이오닉5", "아이오닉5 N", "아이오닉6", "코나EV"]:
    a("현대자동차", p, "10월 200만원 할인(전월 100만원에서 100만원 추가)")
for p in ["넥쏘", "제네시스 GV60"]:
    a("현대자동차" if p == "넥쏘" else "제네시스", p, "10월 신규 300만원 할인")
for p in ["제네시스 G70/G70 슈팅브레이크/GV70/GV70 EV/GV60", "제네시스 G80/GV80/GV80 쿠페/G80 EV"]:
    a("제네시스", p, "수입차·제네시스 보유/렌트/리스 고객 구매 시 " + ("30만원" if "G70" in p else "50만원") + " 지원")
a("제네시스", "제네시스 G90", "수입차·제네시스 보유/렌트/리스 고객 구매 시 100만원(50만원 할인+50만 캐시백)")
a("현대자동차", "아이오닉5/아이오닉6/코나EV/넥쏘/GV60/G80 EV/GV70 EV", "차령 10년 이상 보유 고객 교체 시 30만원 할인")
a("현대자동차", "마이티/파비스", "차령 10년 이상 보유 고객 교체 시 50만원 할인")
a("현대자동차", "포터", "차령 7년 이상 소형트럭 보유 고객 50만원, 그 외 7년 이상 차량 보유 시 30만원 할인")
a("기아", "EV9", "EV 페스타 250만원 지원(차량가격 또는 충전기 설치비)")
a("기아", "봉고 EV", "EV 페스타 200만원 지원; 소상공인·농축수협 조합원 충전기 설치비 70만원 또는 미설치 시 차량가 30만원 또는 ICCB 케이블")
a("기아", "니로 EV", "EV 페스타 100만원 지원")
a("기아", "니로 플러스 택시", "EV 페스타 100만원 지원")
a("기아", "K5 LPG 프레스티지", "일반 고객 또는 렌터카 출고 시 50만원 할인")
a("기아", "K8 (24년형, LPG 포함)", "200만원 할인(구형 모델)")
a("기아", "K8 하이브리드 (24년형)", "300만원 할인(구형 모델)")
a("기아", "더 뉴 EV6", "24년 이내 출고 개인/개인사업자 대상 이전차량 처리·금리변동·잔가 부담 제로 프로그램")
a("르노코리아", "QM6 (2025년형)", "특별 혜택 200만원, 전시장 프로모션·재구매 20만원 포함 최대 340만원")
a("르노코리아", "QM6 SP (25년형)", "특별 혜택 100만원 + MFSK 할부 이용 시 100만원 추가")
a("르노코리아", "아르카나 E-Tech 하이브리드 테크노", "10월 290만원 할인(친환경차 세제혜택 기준), 하이브리드 구매 50만원 특별 혜택, 최대 140만원 추가 할인 가능")
a("르노코리아", "아르카나 E-Tech 하이브리드 아이코닉", "10월 180만원 할인(친환경차 세제혜택 기준), 스마트 할부(24개월 이상, 원금 1500만원 이상) 시 혜택 100만원")
a("르노코리아", "아르카나 (비 E-Tech)", "5년 이상 노후차 보유 고객 30만원 특별 프로모션")
a("르노코리아", "그랑 콜레오스 E-Tech 하이브리드", "별도 할인 없음, 잔가보장 프로그램")
a("KG모빌리티", "토레스 EVX / EVX 밴", "3D 어라운드 뷰 모니터링 시스템(100만원 상당) 무상 지원; 선수금 50% 3.5%/30% 4.5%/0% 5.5% 60개월 할부")
a("KG모빌리티", "코란도 EV", "300만원 혜택; 전기차 지역 할인제 지자체 50만원 추가 보조금; 60개월 할부 프로그램")
a("KG모빌리티", "더 뉴 토레스", "3D 어라운드 뷰 모니터링(100만원 상당)과 유류비 50만원")
a("KG모빌리티", "렉스턴 스포츠&칸", "4WD 시스템(200만원 상당) 지원")
a("KG모빌리티", "렉스턴 / 티볼리 에어", "최대 150만원 혜택")
a("KG모빌리티", "코란도", "100만원 혜택")
a("KG모빌리티", "티볼리", "50만원 혜택")
a("KG모빌리티", "렉스턴 Summit", "렉스턴 보유 고객 구매 시 3D 어라운드 뷰 모니터링(101만원) 무상 장착")
a("쉐보레", "트랙스 크로스오버", "4.5% 최대 36개월/4.9% 최대 60개월/5.2% 72개월(선수율 20%) 할부")
a("쉐보레", "트레일블레이저 (2025년형)", "콤보 할부 현금 50만원 지원 + 5.9% 36개월 또는 6.5% 72개월 할부")
a("쉐보레", "콜로라도 (신형)", "6.0% 최대 72개월 할부")
a("쉐보레", "트랙스 크로스오버/트레일블레이저 (업그레이드/오너 프로그램)", "스파크 보유 고객 최대 100만원, 쉐보레 보유 고객 50만원, 경소형차 보유 고객 20만원(중복 불가)")
a("GMC", "트래버스", "콤보 할부 시 차량금액 최대 15% 지원, 일시불 최대 300만원, 특정 색상(블랙체리·스털링 그레이) 100만원 추가")
a("쉐보레", "타호", "콤보 할부 시 차량금액 15% 지원, 일시불 최대 400만원 지원, 사업자 100만원 추가")
a("GMC", "시에라", "5.5% 최대 36개월/6.0% 최대 72개월 할부, 아발론 화이트 150만원/인디고 블루 50만원 추가, 사업자 100만원 추가")
items = []
for i, (v, p, c) in enumerate(R, 1):
    m = re.search(r"(\d+)만\s?원", c)
    items.append({
        "item_id": f"{SID}-{i:04d}", "category": "auto", "source_id": SID, "unit": None,
        "vendor": v, "channel": "위키트리(10월 프로모션 기사)", "product": p, "model_code": None,
        "buy_url": URL, "image_url": None, "rating": None, "review_count": None, "event_url": URL,
        "claimed_original_price": None, "sale_price": None, "claimed_discount_pct": None,
        "conditions": c, "sources": [URL],
    })
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"category": "auto", "source_id": SID, "collected_at": "2026-10-31",
           "issues": ["기사 작성일 2024-10-07(2024년 10월 프로모션): 2026 코그페 행사 아님", "가격 정보 없음(프로모션 금액만 conditions 에 기재)"],
           "items": items}, open(OUT, "w", encoding="utf8"), ensure_ascii=False, indent=2)
print(len(items))
