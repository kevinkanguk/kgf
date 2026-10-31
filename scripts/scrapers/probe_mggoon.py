import requests,json,sys
s=requests.Session();s.headers['User-Agent']='Mozilla/5.0'
s.get('https://mggoon.co.kr/Goods/List?cno=38&pageType=DEFAULT')
p=dict(tagno=0,cno=38,isview='Y',istime=False,islike=False,sval='',sortby=0,usortby=4,DateDuration=7,eventidx=0,gpg_idx=0,pageType='DEFAULT',listType='DEFAULT',listLayoutType='3_DIV1',bannerUseYN='Y',bannerIdx=7,bannerType='SLIDE',recommendUseYN='N',recommendIdxs='',userLayoutSettingidx='0',recommendUserLayoutSettingidx='0',curOS='AOS',sc_idx=0,isgift=False,page=1,rows=24)
r=s.post('https://mggoon.co.kr/Goods/GetGoodsListNew',json={'param':p,'list_template_name':'/Views/Templates/LIST/3_DIV.cshtml','igm_idx':'12'},headers={'X-Requested-With':'XMLHttpRequest'})
print(r.status_code,len(r.text));open('E:/090_ETC/kf/data/cache/html/food-mggoon-soosan/api1.json','w',encoding='utf8').write(r.text)
print(r.text[:1500])
