"""Notify search engines (Bing, Yandex, Seznam, Naver via IndexNow) that the site changed.

Run after each push:  python3 indexnow.py
Submits every URL in docs/sitemap.xml. Safe to run repeatedly; failures are reported, not fatal.
"""
import json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "site-config.json")))
key = cfg.get("indexnow_key")
host = "rates.buildocrat.store"
urls = re.findall(r"<loc>(.*?)</loc>", open(os.path.join(HERE, "docs", "sitemap.xml"), encoding="utf-8").read())
body = json.dumps({"host": host, "key": key, "keyLocation": f"https://{host}/{key}.txt", "urlList": urls[:10000]}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("IndexNow:", r.status, f"({len(urls)} URLs submitted)")
except Exception as ex:
    print("IndexNow not sent:", ex)
    sys.exit(0)
