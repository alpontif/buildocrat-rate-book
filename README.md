# Nigeria Construction Rate Book — Buildocrat

A public construction price book for Nigeria: material, labour and plant prices, plus 160 first-principles BoQ unit rates. Abuja is the base location, with factors for 11 others. Every composite rate is recalculated in the visitor's browser from its build-up.

## What's in this repository

| File | Purpose |
|---|---|
| `rate-data.json` | **Source of truth.** Every price, labour grade, plant item and build-up. The weekly update edits only this file. |
| `engine.js` | Rate maths (materials × waste, labour hours × all-in rate, plant days × all-in rate). |
| `page_template.html` | Page layout and design. |
| `assemble.py` | Builds the website into `docs/` from the three files above. |
| `docs/index.html` | The built website (what visitors see). |
| `docs/rate-data.json` | Public copy of the data, for anyone who wants the raw numbers. |

## One-time setup (about 20 minutes)

### 1. Put the files on GitHub
1. Create a free account at github.com if you don't have one.
2. Create a new **public** repository, for example `rate-book`.
3. Upload every file in this folder, including the `docs` folder.

### 2. Turn on GitHub Pages
1. In the repository, go to **Settings → Pages**.
2. Under *Build and deployment*, choose **Deploy from a branch**.
3. Choose branch `main` and folder `/docs`, then save.
4. After a minute the site is live at `https://<your-username>.github.io/rate-book/`.

### 3. Use your own domain (live setup: `rates.buildocrat.store`)
1. In **Settings → Pages → Custom domain**, enter `rates.buildocrat.store` and save. GitHub adds a `CNAME` file to `docs/`.
2. At your domain registrar or DNS provider, add a DNS record:
   - Type `CNAME`, name `rates`, value `<your-username>.github.io`
3. Wait for DNS to update (usually minutes, sometimes a few hours), then tick **Enforce HTTPS** in Settings → Pages.

To use the root domain (`buildocrat.store`) instead, add four `A` records pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and `185.199.111.153`.

### 4. Let Claude update it every week
1. In claude.ai, go to **Settings → Connectors** and connect **GitHub**, granting access to this repository.
2. Tell Claude the repository name (for example `buildocrat/rate-book`).

Claude then changes the weekly price-refresh task to do the following:
- research the prices;
- edit `rate-data.json`;
- run `python3 assemble.py`;
- commit and push.

GitHub Pages republishes automatically within a minute of each push.

## Updating by hand

Edit prices in `rate-data.json`, then run:

```
python3 assemble.py
```

Commit both `rate-data.json` and the `docs/` folder.

Field names in `rate-data.json`:

| Field | Meaning |
|---|---|
| `r` | rate in naira |
| `lo`, `hi` | low and high of the range |
| `src` | source |
| `ev` | evidence date |
| `set` | date the price was set |
| `conf` | HIGH, MEDIUM or LOW |
| `pr` | previous rate |

Entries that contain `k` are derived from another price, so never edit those.

## Other hosts
Netlify or Cloudflare Pages work the same way. Connect the repository and set the publish directory to `docs`, with no build command. Automatic deploys on each push keep the site current.

## Installing the site as an app
The website is installable:
- **Android (Chrome)** and **desktop (Chrome/Edge):** use the **Install app** button in the header, or the install icon in the address bar.
- **iPhone/iPad (Safari):** tap **Install app** for instructions. You tap **Share**, then **Add to Home Screen**.

Once installed, it opens full-screen and works offline with the last prices it downloaded.

`assemble.py` writes three files for this:
- `docs/manifest.webmanifest`
- `docs/sw.js`, the offline cache
- the icons in `docs/icons/`, made by `make_icons.py`

The cache version changes on every rebuild. When a weekly price update is pushed, installed apps pick it up the next time they're online.

## Search engines and AI assistants (SEO)
`assemble.py` also builds a crawlable static site from `rate-data.json`. It uses `site_build.py`, with `engine_py.py` as the Python copy of the rate maths; the two engines are checked to agree to the naira.

**Pages**
- Home: the interactive rate book, with pre-rendered content so crawlers see it without JavaScript.
- `/prices/` plus 15 price pages (cement, iron rods, blocks, sand, granite, roofing, tiles, paint, timber, diesel, tanks, solar, ready-mix, cables, doors and windows).
- `/rates/` plus one page per BoQ rate (160).
- `/labour/`, `/plant/`, `/locations/` (12 cities), and the bungalow cost guide.
- `/methodology/`, `/about/`, `/updates/` and `/data/`.

**Files for search engines and AI**
- `sitemap.xml`
- `robots.txt`, which explicitly allows the search and AI crawlers
- `llms.txt` and `llms-full.txt`, plain-text versions for AI assistants
- `feed.xml`, an Atom feed of the weekly updates
- `og.png`, the social preview image, redrawn each week with the current prices
- CSV and JSON downloads in `/data/`
- `404.html`

**Structured data:** JSON-LD for Organization, WebSite, Dataset, WebPage, BreadcrumbList and FAQPage.

**Settings (`site-config.json`)**
- `google_site_verification`: the token from the Google Search Console HTML-tag method.
- `bing_site_verification`: the token from Bing Webmaster Tools.
- `indexnow_key`: keep as is.

**IndexNow:** `.github/workflows/indexnow.yml` notifies Bing and other IndexNow search engines after every data push.

## Measuring performance
- **Google Analytics 4:** put the Measurement ID (`G-XXXXXXX`) in `site-config.json` as `ga4_measurement_id`, then run `python3 assemble.py` and push. Nothing is tracked until this is set.
  - Custom events tracked: `whatsapp_click` (Price Lock leads; mark it as a key event), `data_download`, `open_rate_book`, `buildup_open`, `estimator_add_line`, `tab_view`, `location_change` and `app_installed`.
- **Cloudflare Web Analytics** (optional, cookieless): set `cloudflare_web_analytics_token`.
- **Google Search Console and Bing Webmaster Tools** give search queries, impressions, clicks and ranking position.
- **Privacy notice:** `/privacy/` (built automatically).
