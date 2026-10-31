import json
S=[]
def add(sid,channel,url,kind,est,access,note):
    S.append({"source_id":sid,"category":"mall","channel":channel,"url":url,"kind":kind,"est_items":est,"access":access,"note":note})
FOOD=" 식품류: food 카테고리와 중복 가능."
# KGF official
add("mall-kgf-sme-online","코그페 스토어(/sme) 온라인입점","https://koreagrandfestival.kr/sme","listing",47,"static",
    "전체 491개 업체 중 is-online=Y 47곳(스마트스토어/브랜드몰 링크). data-online-url 로 추출, 업체별 상품 목록은 외부몰. 오프라인 397곳은 기념품/음료 증정 등 가격 없음 -> 제외. 'TEST0914' 테스트 데이터 행 포함(제외 필요). 추출 결과 data/cache/html/sme_online.json")
add("mall-kgf-discountcate","코그페 공식 분야별 할인정보","https://koreagrandfestival.kr/discountcate","notice",0,"static","11개 분야 안내 카드(여행/문화/국가유산/농축산물/한우/자동차·가전/유통·서비스/수산물/중소·소상공인/면세점/지역특산물). 가격 품목 없음, 타 카테고리 링크만")
add("mall-kgf-event-etc","코그페 기타이벤트(배달앱 쿠폰)","https://koreagrandfestival.kr/event/etc","notice",0,"static","배달앱(땡겨요, 먹깨비 등) 쿠폰 공지 11건. 상품 가격 없음 -> 수집 제외 권장")
add("mall-kgf-event-regional","코그페 지역상권(핵점포) 행사","https://koreagrandfestival.kr/event/regional","notice",0,"static","오프라인 지역행사 일정. 가격 품목 없음 -> 제외 권장")
# 11st
for tid,nm,n,en,food in [(1756462,"신선식품",74,"fresh",True),(1756467,"가공식품",74,"processed",True),(1756468,"건강/다이어트식품/의료용품",84,"health",True),(1756469,"출산/유아용품/장난감",77,"baby",False),(1757688,"리빙/생활문화",24,"living",False),(1757689,"뷰티/헬스",29,"beauty",False),(1757690,"패션",32,"fashion",False)]:
    add(f"mall-11st-sosang-{en}","11번가",f"https://plan.11st.co.kr/plan/front/exhibitions/2211141/themes/{tid}/products","listing",n,"static",
        f"2026 소상공인 온라인 판로지원 기획전(2211141) 탭 '{nm}'. POST(Referer=기획전 URL, X-Requested-With=XMLHttpRequest)로 JSON 전량 반환(themeProducts: productNo/finalPrice/sellPrice/discountRate). curl 검증됨."+(FOOD if food else ""))
# gmarket
base="https://rpp.gmarket.co.kr/?exhib=280311"
for comp,sid,nm,n,acc,fd in [("27870404","fresh","신선식품1~5(5탭)",120,"static",True),("27870406","processed","가공식품1~5(5탭)",120,"static",True),("27870408","health","건강식품1~3(3탭)",96,"static",True),
    ("27870410","digital","디지털(allitem3, 정적 HTML에 상품 없음-동적 로딩)",None,"js",False),("27870412","living","생활용품1·2/건강용품/반려취미기타/육아용품/인테리어(6탭)",144,"static",False),("27870414","beauty-fashion","뷰티1·2/패션1·2/바디·헤어(5탭)",120,"static",False)]:
    add(f"mall-gmarket-kgf-{sid}","G마켓",f"{base}#comp_{comp}","listing",n,acc,
        f"코리아그랜드세일페스타 기획전 섹션 {nm}. 정적 HTML(5.5MB)에 itemNo/goodscode/origin_price/coupon_price 포함(utparam-url). 탭당 24~32개로 보이며 '더보기' 추가 로딩 여부 미확인."+(FOOD if fd else "")+" 공통쿠폰: 12% 최대1만원(1만원 이상, 선착순 5000명/일).")
# lotteon
for en,nm,n,fd in [("fresh-fruit","신선식품(과일/채소/쌀)",438,True),("fresh-meat","신선식품(수산/정육/계란)",421,True),("processed","가공식품",712,True),("living","리빙",539,False),("beauty","뷰티",121,False),("fashion","패션/잡화",841,False),("hobby-kids-pet","취미/유아동/반려",192,False)]:
    note=f"소상공인과 함께하는 가을맞이 쇼핑특별전(112088) 탭 '{nm}' 표시 건수 {n}(브라우저로 탭 클릭해 확인). 상품 목록은 JS 렌더(Incapsula 보호), 60개씩 보기/정렬 지원."
    if n>300: note+=" 300개 초과: 정렬(낮은가격순/판매량순 등)·페이지 구간으로 분할 수집 필요."
    if fd: note+=FOOD
    add(f"mall-lotteon-sosang-{en}","롯데온",f"https://www.lotteon.com/display/planV2/planDetail/112088#tab={en}","listing",n,"js",note)
# skstoa
add("mall-skstoa-kgf","SK스토아","https://www.skstoa.com/plan/event/detail/2026103519","listing",206,"static",
    "코리아 그랜드페스티벌 기획전. 탭: 식품/가구·리빙/가전·디지털/생활·주방/패션·뷰티. 첫 60개는 정적 HTML(ga-prd-data p-id/p-price/p-name, 정상가·할인율 포함), 총 206개(planShopTotalCount=206)는 /plan/planDetail/more 페이징(60개씩)으로 추가 로딩. 상품 URL /display/goods/<id>.")
# hmall
b="https://www.hmall.com/md/api/cache?url=/api/hf/dp/v1/sect-mng/plansale-ancr-paging&sectId=2811083&sortType=sect_disp&listSize=20&deviceInfo=pc"
hn="현대Hmall 소상공인 기획전 '물가안정 프로젝트'(sectId 2811083). JSON API(curl 가능, Referer 필요). itemList: slitmCd,slitmNm,sellPrc,bbprc(최종가),copnDcAmt 등. 전체 목록(page=N, 20개/페이지, 약 107페이지)을 받아 sectNm 으로 필터."
add("mall-hmall-sosang-coupon-food","현대Hmall",b+"&page=1#sect=food","listing",164,"static",hn+" 섹션 '식품'(쿠폰 적용 섹션)."+FOOD)
add("mall-hmall-sosang-coupon-living","현대Hmall",b+"&page=1#sect=living","listing",139,"static",hn+" 섹션 생활용품 70 + 반려동물용품/취미 52 + 가전/가구/침구 12 + 스포츠/레저 1 + 선착순할인쿠폰 4.")
add("mall-hmall-sosang-coupon-beauty-fashion","현대Hmall",b+"&page=1#sect=beauty-fashion","listing",135,"static",hn+" 섹션 뷰티 78 + 패션/패션잡화 57.")
for i,(a,z) in enumerate([(1,300),(301,600),(601,900),(901,1200),(1201,1500),(1501,1739)],1):
    n=min(z,1739)-a+1
    add(f"mall-hmall-sosang-reco-{i}","현대Hmall",b+f"&page=1#reco={a}-{min(z,1739)}","listing",n,"static",hn+f" 섹션 '추천상품(쿠폰 미적용)' 총 1739개 중 {a}~{min(z,1739)}번째(전체 페이징 순서에서 해당 sectNm만 추려 자른 구간). 쿠폰 미적용 상시 상품 포함: 행사 할인 해당 여부 확인 필요.")
# nsmall
add("mall-nsmall-sosang","NS몰","https://m.nsmall.com/store/atypical/1009576266","listing",76,"js","NS홈쇼핑 소상공인 물가안정 특가전. 브랜드/주제 그룹별 섹션(한유원 정부지원 소상공인 특가전 등)으로 구성, 스크롤 후 상품 링크 76개 확인(/goods/<id>). 쿠폰 10% 등 조건 상품 다수. 식품 위주."+FOOD)
# grip
add("mall-grip-kgf","그립","https://www.grip.show/event/korea-2026","listing",100,"js","코세페 기획전(탭 전체상품/패션/뷰티/식품/생활잡화) 무한스크롤. 최소 100개 확인(탭별 정확한 수 미확인, 탭 전환 시 누적 카운트라 신뢰 불가). 상품 URL /product/<id>. 탭별 분할 수집 권장.")
# ssg
for en,nm in [("md-pick","MD's Pick"),("health-honey","건강식품/꿀"),("meat-fish","축산/수산/건식품"),("veg-fruit-grain","채소/과일/양곡"),("drink-dairy","음료/커피차/유제품"),("snack-bakery","과자/베이커리/떡"),("meal-kimchi","간편식/김치/반찬"),("seasoning-noodle","조미료/면/통조림")]:
    add(f"mall-ssg-sosang-{en}","SSG닷컴",f"https://www.ssg.com/plan/planShop.ssg?dispCmptId=6000465146#tab={en}","listing",73,"js",f"[E] 소상공인 브랜드대전 탭 '{nm}'. 전체 스크롤 시 고유 상품 약 588개(8개 탭 합계; 탭별 73은 균등 추정치로 실제 편차 있음). 식품 전용 기획전."+FOOD+" 일부는 '~12%'/'외' 형태 묶음(모음전) 상품.")
# epost
pg=[(1,7),(8,14),(15,21),(22,28),(29,35),(36,42),(43,49),(50,56),(57,60)]
for i,(a,z) in enumerate(pg,1):
    n=(z-a+1)*40 if z<60 else (z-a)*40+35
    add(f"mall-epost-kgf-p{i}","우체국쇼핑",f"https://mall.epost.go.kr/fo/display/plnbefDspyNewView.do?plnbefId=10027801#pages={a}-{z}","listing",n,"static",f"우체국쇼핑 코그페 기획전(10027801) 페이지 {a}~{z} (40개/페이지, 총 60페이지 약 2395개). POST plnbefId=10027801&pageIndex=N&pageUnit=40 으로 정적 HTML 수신 확인(curl). goodsDetailView('EAxxxxxxx',...)로 상품코드 추출. 농축수산 위주."+FOOD)
# zigzag
for en,nm,n in [("cardigan-outer","가디건&아우터",294),("blouse-shirt","블라우스&셔츠",100),("pants","팬츠",166),("skirt-dress","스커트&원피스",250),("tops","상의",486),("denim","데님",53),("innerwear-homewear","이너웨어&홈웨어",101),("jewelry","주얼리",167),("bag","가방",79),("shoes","신발",90),("fashion-acc","패션잡화",120),("etc","기타",24)]:
    note=f"지그재그 대국민 소비축제 카테고리 '{nm}' 표시 건수 {n}(HTML 텍스트). 상품은 JS/API(api.zigzag.kr/api/2) 로딩, MD 추천순 '상품 더 보기' 페이징. 패션 카테고리 겹침 가능."
    if n>300: note+=" 300개 초과: 정렬/구간 분할 필요."
    add(f"mall-zigzag-kgf-{en}","지그재그",f"https://zigzag.kr/events/39082ee6-17bc-48bf-9b55-d466cc13f059#cat={en}","listing",n,"js",note)
# oasis
add("mall-oasis-kgf","오아시스마켓","https://www.oasis.co.kr/event/2026/koreaGrandFestival_1029","listing",70,"js","코리아 그랜드 페스티벌 기획전. 스크롤 후 링크 70개 확인했으나 다수가 검색어 링크(/product/search?keyword=...)라 실제 상품 수는 미확인. 정적 HTML엔 상품 ID 24개. 식품(신선) 위주."+FOOD)
# wconcept
add("mall-wconcept-kgf","W컨셉","https://display.wconcept.co.kr/rn/desktop/promotion/132","brand_event",None,"js","코리아 그랜드 페스티벌 기획: 라이프/뷰티 브랜드 쿠폰(최대 9만원)·브랜드 목록 중심. 접속 시점에 '추천 가능한 상품이 없어요'로 상품 0개 렌더(키친/홈패브릭/컬쳐·반려/메이크업/스킨케어/헤어바디/이너뷰티/가전 탭). 브랜드 단위 확인 필요. 원 링크의 previewDate 파라미터는 제거함.")
# naver
add("mall-naver-kgf","네이버쇼핑","https://shopping.naver.com/festa/onsale/6a7e9f9d233b4473b033f8c8","listing",None,"js","curl 접근 시 maintenance 페이지로 리다이렉트, 브라우저 패널은 도메인 제한으로 열 수 없음. 봇 차단 우회는 시도하지 않음. 06_browser_fallback 또는 사용자 브라우저에서 확인 필요.")
# gov
add("mall-kshoppingfesta","동행축제(k-shoppingfesta.org)","https://k-shoppingfesta.org","listing",None,"js","Vue SPA(gachi-portal-front-vue), JS 없이 내용 없음. 참여 쇼핑몰/상품 API 미확인 -> 브라우저 확인 필요.")
add("mall-ksalefesta","K-세일페스타(k-salefesta.co.kr)","https://www.k-salefesta.co.kr","listing",None,"js","curl 연결 실패(HTTP 000). 접속 가능 여부·참여몰 목록 미확인.")
add("mall-ilovegohyang-gift","고향사랑e음 답례품몰","https://www.ilovegohyang.go.kr/goods/index-main.html","listing",None,"js","Vue 렌더, 답례품은 기부 포인트(P) 표시. 정가 대비 할인 개념이 약해 검증 대상 여부 판단 필요.")
add("mall-khstore-heritage","K-Heritage 스토어(국가유산진흥원)","https://khstore.or.kr/","listing",None,"static","공식 about 페이지 링크. cafe24형 쇼핑몰, 상품 수 미집계. 국가유산 카테고리와 중복 가능.")
json.dump({"category":"mall","sources":S},open("E:/090_ETC/kf/data/sources/mall.json","w",encoding="utf8"),ensure_ascii=False,indent=2)
ids=[s["source_id"] for s in S]; assert len(ids)==len(set(ids)); print(len(S), sum(s["est_items"] or 0 for s in S))
