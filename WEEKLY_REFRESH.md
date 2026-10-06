# Weekly Rate Book refresh

Weekly price refresh for Buildocrat's "Nigeria Construction Rate Book", owned by Engr. Akolade Maruf Ibrahim (Kola), Abuja. The GitHub repository alpontif/buildocrat-rate-book is the SOURCE OF TRUTH. GitHub Pages serves its /docs folder at https://rates.buildocrat.store: about 388 crawlable, SEO-optimised pages. The repo is also mirrored to the claude.ai artifact https://claude.ai/artifact/LmumxCyhreY7tiGE3sXZcC. Goal: re-research key Nigerian construction prices, update rate-data.json, rebuild the whole site, push (GitHub then republishes and notifies search engines), and republish the artifact.

HOW THIS RUNS: Kola starts this by hand in a chat each Monday. Work in the cloud workspace.

STEPS
1. Attach the repo with add_repo (owner "alpontif", repo "buildocrat-rate-book", access "push"). If no add_repo tool is available, stop and tell Kola the repo could not be attached; do not research or publish anything.
2. Clone it: git clone https://github.com/alpontif/buildocrat-rate-book (retry once after 30s if GitHub returns 503). Check that python3 and Pillow work; if `import PIL` fails, run pip install pillow --break-system-packages.
3. Read the ARTIFACT FIRST: Artifact action "read", url https://claude.ai/artifact/LmumxCyhreY7tiGE3sXZcC. Its page embeds the data in <script id="rate-data" type="application/json">. Compare its resources[], labour[], plant[] and changelog[] with the repo's rate-data.json. Any line or changelog entry that is newer in the artifact (a later "set" date or a changelog date the repo lacks) came from an earlier run whose push failed. Copy those entries into rate-data.json before researching, and note them in this week's changelog as "restored from artifact". Never copy items[], sources, locations or any code.
4. rate-data.json schema:
   - meta{updated, fx, fxNote, watch[]}, params, changelog[].
   - resources[] are materials, tools and equipment for sale: c=code, d=description, u=unit, r=rate in naira, lo, hi, src, ev=evidence date, set=date price set, conf=HIGH/MEDIUM/LOW, pr=previous rate. Entries with "k" are DERIVED from another code (k.b base, k.f factor, optional k.s spread); never edit those. About 220 imported items are derived from resource M-FX-USD (naira per US dollar), so they move automatically with it. Codes M-EQ-* are construction equipment PURCHASE prices (new and used), separate from plant[] hire rates.
   - labour[]: day=daily wage, lo, hi, or mon=monthly for Staff.
   - plant[]: dry=dry hire/day, lo, hi, lpd=fuel L/day.
   - items[], sources, locations and ALL code/template files: do not touch.
5. Research current prices, Abuja base, using WebSearch/WebFetch and preferring sources dated within the last 14 days. Cover at least:
   - M-CEM-01 (OPC 50kg adopted average) and brand lines M-CEM-07/08/09.
   - Rebar per tonne: M-STL-01, M-STL-02, M-STL-03.
   - M-FUE-01 diesel and M-FUE-02 petrol pump prices, and M-FUE-03 LPG per kg.
   - Aluminium roofing per m2: M-RF-01, M-RF-02, M-RF-10, M-RF-11.
   - M-BLK-01 (9" block, Abuja).
   - M-AGG-01 (sharp sand 20t) and M-AGG-07 (granite 30t).
   - The CBN NFEM naira/dollar rate: set meta.fx AND resource M-FX-USD (r = the rate, lo/hi = the week's observed low/high, plus src/ev/set/pr as in step 6). These two must always agree.
   Also spot-check 2-3 LOW-confidence lines each week, rotating categories (e.g. cables M-EL-*, plumbing M-PL-*, plant dry-hire, tools M-TL-*, geosynthetics M-GS-*, marine M-MR-*, water M-WT-*, equipment for sale M-EQ-* using Jiji.ng category listings such as jiji.ng/274-excavators, jiji.ng/274-bulldozers, jiji.ng/274-wheel-loaders, jiji.ng/274-graders, jiji.ng/274-cranes, jiji.ng/274-forklifts). Upgrade them only with a dated, credible Nigerian source.
6. For each price supported by a dated source:
   - set pr = old r;
   - set new r, and lo/hi to the observed range;
   - set src = short source description with date, ev = evidence date YYYY-MM-DD, set = today;
   - adjust conf to match the evidence.
   Guard rail: a move of more than 25% needs two independent sources; otherwise leave the price unchanged and report it. If you cannot verify a price, leave its entry completely unchanged, including its "set" date.
7. Update meta.updated = today, meta.fx and meta.fxNote (e.g. "CBN NFEM, 5 Oct 2026"). Append one changelog entry {date, note} listing changes in plain words, e.g. "Cement N12,000 -> N11,800/bag; diesel N1,900 -> N1,870/L", or "No verified price changes this week". Edit rate-data.json with a short Python script that reads the file, changes only the fields above, and writes it back with json.dump(..., separators=(",", ":"), ensure_ascii=False) and encoding="utf-8". Never retype the file's content.
8. In the repo, run python3 assemble.py. It rebuilds rate-book.html, every static page, sitemap.xml, feed.xml, llms.txt, llms-full.txt, the CSV/JSON downloads, the service worker and og.png. Confirm the output reports about 388 pages and no errors.
9. git add -A rate-data.json docs, commit with the message "Weekly price refresh <date>: <short summary>" (author Claude <noreply@anthropic.com>), then git pull --rebase origin main and git push origin main. GitHub Pages republishes, and the repo's GitHub Action notifies search engines through IndexNow automatically.
10. Republish the artifact with the Artifact tool: action "publish", url https://claude.ai/artifact/LmumxCyhreY7tiGE3sXZcC, file_path = the repo's rate-book.html. If the publish is refused with a conflict, read the live version, merge any further data-only changes as in step 3, rebuild, commit and push again, then publish the rebuilt file.
11. Finish with a summary for Kola, under 10 lines: what changed (old -> new, with sources), anything restored from the artifact, anything suspicious you did not apply, any LOW lines upgraded, and whether the push and publish succeeded. 

Rules: never invent prices; every changed number needs a real dated source. Never create a new repo or artifact. Do not alter page design, code or generated pages by hand. Never delete files or discard work in Kola's folders. If the push is refused, report that plainly, still republish the artifact, and do not lose the data changes (include the key changes in the summary).
