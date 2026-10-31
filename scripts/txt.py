import re,sys
def txt(f):
    t=open(f,'rb').read()
    try:s=t.decode('utf8')
    except: s=t.decode('euc-kr','replace')
    s=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
    s=re.sub(r'<a[^>]*href="([^"]+)"[^>]*>',r' [\1] ',s)
    s=re.sub(r'<img[^>]*alt="([^"]*)"[^>]*>',r' {\1} ',s)
    s=re.sub(r'<[^>]+>',' ',s);return re.sub(r'\s+',' ',s)
for f in sys.argv[1:]:
    open(f+'.txt','w',encoding='utf8').write(txt(f))
