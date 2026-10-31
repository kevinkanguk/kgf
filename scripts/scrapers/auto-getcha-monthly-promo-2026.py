# Source page returned 403 to requests; WebFetch showed body has no per-model/trim prices (only unrelated recommended-content titles).
import json
SID="auto-getcha-monthly-promo-2026"
out={"category":"auto","source_id":SID,"collected_at":"2026-10-31","items":[],
 "issues":["requests got 403; WebFetch body has no model/trim discount data (article text only); recommended-content titles are unrelated items, not collected"]}
json.dump(out,open(f"data/raw/catalog/auto/{SID}.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
