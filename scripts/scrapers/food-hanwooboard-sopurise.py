# 공지(seq=15447)의 등급x부위 상한가 표를 카탈로그로 저장 (사이트가 자동 요청에 404 응답하여 수동 확인값 사용)
import json, os
SID="food-hanwooboard-sopurise"
URL="https://www.hanwooboard.or.kr/pages/notification/notice/view.html?seq=15447"
IMG="https://www.hanwooboard.or.kr/upload_file/editor/20260126095710ZXJPTQ.png"
P={"1+":(9370,4640,3480),"1":(8430,4430,3360),"2":(5830,4110,2990)}
CUTS=["등심","양지","불고기·국거리용"]
items=[];n=0
for g,v in P.items():
    for c,p in zip(CUTS,v):
        n+=1
        items.append({"item_id":f"{SID}-{n:04d}","category":"food","source_id":SID,"unit":"100g","vendor":"한우자조금관리위원회",
         "channel":"소프라이즈 한우세일(GS리테일·이마트·홈플러스·롯데마트·쿠팡 등 21개 업체)",
         "product":f"한우 {g}등급 {c} 100g" if g!="1+" else f"한우 1+등급 {c} 100g","model_code":None,
         "buy_url":URL,"image_url":IMG,"rating":None,"review_count":None,"event_url":URL,
         "claimed_original_price":None,"sale_price":p,"claimed_discount_pct":None,
         "conditions":"제시 가격 이하로 판매(상한가), 10/28~11/8, 업체별 기간·재고 상이",
         "sources":[URL],"verify_status":None,"verify_note":None,"confidence":None})
out={"category":"food","source_id":SID,"collected_at":"2026-10-31","items":items}
path=os.path.join(os.path.dirname(__file__),"..","..","data","raw","catalog","food",SID+".json")
json.dump(out,open(path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(len(items))
