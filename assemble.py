"""Build the Nigeria Construction Rate Book.

Source of truth: rate-data.json (prices), engine.js (rate maths), page_template.html (layout).
Outputs:
  rate-book.html      - fragment for the claude.ai artifact
  docs/index.html     - full standalone page for your own website (GitHub Pages serves /docs)
  docs/rate-data.json - public copy of the data
Run:  python3 assemble.py
"""
import json, os, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(HERE, *a)

tpl = open(p("page_template.html"), encoding="utf-8").read()
eng = open(p("engine.js"), encoding="utf-8").read()
raw = open(p("rate-data.json"), encoding="utf-8").read()
data = json.loads(raw)
body = tpl.replace("__ENGINE__", eng).replace("__DATA__", raw.replace("</", "<\\/"))

# 1) artifact fragment
open(p("rate-book.html"), "w", encoding="utf-8").write(body)

# 2) standalone website: crawlable multi-page site + SEO/AI files (site_build.py)
from site_build import Site, EXTRA_CSS, BASE, HUBS
cfg = json.load(open(p("site-config.json"))) if os.path.exists(p("site-config.json")) else {}
os.makedirs(p("docs"), exist_ok=True)
site = Site(p("docs"), data, cfg)
bung = site.build_all(tpl)
upd = data["meta"]["updated"]
title_end = body.index("</title>") + len("</title>")
rest = body[title_end:]
watch, view, summary, browse = site.home_inserts(bung)
def inject(src, a, b):
    assert src.count(a) == 1, a
    return src.replace(a, b)
rest = inject(rest, '<section class="watch" id="watch" aria-label="Key price indicators"></section>',
              f'<section class="watch" id="watch" aria-label="Key price indicators">{watch}</section>')
rest = inject(rest, '<main id="view"></main>', f'<main id="view">{view}</main>')
rest = inject(rest, "  </header>\n", "  </header>\n  " + summary + "\n", ) if rest.count("  </header>\n") == 1 else rest
rest = inject(rest, "  <footer>", browse + "\n  <footer>")
home_title = f"Building material prices & BoQ rates in Nigeria ({site.mon}) | Buildocrat Rate Book"
home_desc = (f"Current building material prices in Nigeria as at {site.date_long}: cement {site.primary_sentence('M-CEM-01')}, iron rods, blocks, sand, granite, roofing; "
             f"labour and equipment hire rates; and {len(data['items'])} BoQ unit rates for Abuja, Lagos and 10 more locations. Updated weekly by Buildocrat.")
home_graph = [site.dataset(), {"@type": "WebPage", "@id": BASE + "/", "url": BASE + "/", "name": home_title, "description": home_desc,
              "isPartOf": {"@id": BASE + "/#website"}, "about": {"@id": BASE + "/#dataset"}, "publisher": {"@id": BASE + "/#org"},
              "inLanguage": "en-NG", "datePublished": "2026-09-29", "dateModified": upd, "primaryImageOfPage": BASE + "/og.png"}]
head = f"""<!doctype html>
<html lang="en-NG">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
{site.head_meta(BASE + "/", home_title, home_desc, home_graph)}
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Rate Book">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<style>html{{color-scheme:light dark}}[hidden]{{display:none!important}}img{{max-width:100%}}{EXTRA_CSS}</style>
</head>
<body>
"""
SW_REG = """<script>
if ("serviceWorker" in navigator && window.self === window.top) {
  window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
}
</script>"""
os.makedirs(p("docs"), exist_ok=True)
html = head + rest + "\n" + SW_REG + "\n</body>\n</html>\n"
open(p("docs", "index.html"), "w", encoding="utf-8").write(html)

# 3) installable app: manifest + offline service worker (cache name changes whenever the page changes)
manifest = {
  "name": "Buildocrat Rate Book",
  "short_name": "Rate Book",
  "description": "Nigeria construction prices and BoQ unit rates by Buildocrat, updated weekly.",
  "start_url": "./",
  "scope": "./",
  "id": "./",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#EEF2F0",
  "theme_color": "#0C6A4C",
  "lang": "en-NG",
  "categories": ["business", "productivity", "utilities"],
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
json.dump(manifest, open(p("docs", "manifest.webmanifest"), "w"), indent=2)
ver = hashlib.sha1((html + raw).encode("utf-8")).hexdigest()[:10]
sw = """// Buildocrat Rate Book service worker. Version changes on every rebuild.
const CACHE = "rate-book-%s";
const CORE = ["./", "index.html", "rate-data.json", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    // Network first so weekly price updates show immediately; cached copy when offline.
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return res;
    }).catch(() => caches.match(req).then(r => r || caches.match("index.html"))));
  } else if (url.hostname.endsWith("fonts.googleapis.com") || url.hostname.endsWith("fonts.gstatic.com")) {
    e.respondWith(caches.match(req).then(r => r || fetch(req).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return res;
    })));
  }
});
""" % ver
open(p("docs", "sw.js"), "w").write(sw)
shutil.copy(p("rate-data.json"), p("docs", "rate-data.json"))
print("built", len(body), "bytes; prices as at", upd, "|", len(site.pages), "pages; bungalow", round(bung["total"]))
