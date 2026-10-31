import requests, json
# Naver brand store returns HTTP 429 to non-browser clients; browser pane blocks brand.naver.com. No bypass attempted.
r = requests.get("https://brand.naver.com/koreasusan1", headers={"User-Agent": "Mozilla/5.0"})
print(r.status_code)
