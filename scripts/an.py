import sys; sys.stdout.reconfigure(encoding="utf-8")
import re,sys
for f in sys.argv[1:]:
    t=open(f,'rb').read()
    try:s=t.decode('utf8')
    except: s=t.decode('euc-kr','replace')
    ti=re.search(r'<title[^>]*>(.*?)</title>',s,re.S)
    print('==',f,len(s),(ti.group(1).strip()[:80] if ti else ''))
    for pat in [r'goodsDetail|goods/\d+|/products?/\d+|itemNo|prdNo|goodsNo|item/\d+|productNo|/pd/|/item/']:
        print(' prodlinks',len(set(re.findall(pat,s))), len(re.findall(pat,s)))
