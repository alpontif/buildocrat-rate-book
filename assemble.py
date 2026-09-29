"""Build the Nigeria Construction Rate Book.

Source of truth: rate-data.json (prices), engine.js (rate maths), page_template.html (layout).
Outputs:
  rate-book.html      - fragment for the claude.ai artifact
  docs/index.html     - full standalone page for your own website (GitHub Pages serves /docs)
  docs/rate-data.json - public copy of the data
Run:  python3 assemble.py
"""
import json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(HERE, *a)

tpl = open(p("page_template.html"), encoding="utf-8").read()
eng = open(p("engine.js"), encoding="utf-8").read()
raw = open(p("rate-data.json"), encoding="utf-8").read()
data = json.loads(raw)
body = tpl.replace("__ENGINE__", eng).replace("__DATA__", raw.replace("</", "<\\/"))

# 1) artifact fragment
open(p("rate-book.html"), "w", encoding="utf-8").write(body)

# 2) standalone website
title_end = body.index("</title>") + len("</title>")
title, rest = body[:title_end], body[title_end:]
upd = data["meta"]["updated"]
desc = ("Buildocrat's Nigeria Construction Rate Book: current material, labour and plant prices and "
        f"{len(data['items'])} first-principles BoQ unit rates for Abuja and 11 other locations. Prices as at {upd}.")
head = f"""<!doctype html>
<html lang="en-NG">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{title}
<meta name="description" content="{desc}">
<meta property="og:title" content="Nigeria Construction Rate Book - Buildocrat">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0C6A4C">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='4' fill='%230C6A4C'/%3E%3Ctext x='16' y='23' font-family='Arial' font-weight='700' font-size='20' text-anchor='middle' fill='white'%3EB%3C/text%3E%3C/svg%3E">
<style>html{{color-scheme:light dark}}[hidden]{{display:none!important}}img{{max-width:100%}}</style>
</head>
<body>
"""
os.makedirs(p("docs"), exist_ok=True)
open(p("docs", "index.html"), "w", encoding="utf-8").write(head + rest + "\n</body>\n</html>\n")
shutil.copy(p("rate-data.json"), p("docs", "rate-data.json"))
print("built", len(body), "bytes; prices as at", upd)
