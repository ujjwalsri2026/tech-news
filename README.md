# TechPulse

**A serverless tech news + research digest that rebuilds itself every 6 hours and deploys to GitHub Pages.**

TechPulse scrapes 50 tech publications and 45+ academic/research venues, summarizes every article locally with a neural model (DistilBART), and publishes the result as static JSON. A GitHub Actions cron runs the whole pipeline, commits the data, and deploys to GitHub Pages. There is no server, no database, and no API key.

Live site: **https://ujjwalsri2026.github.io/tech-news/**

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Layout](#project-layout)
- [Data Pipeline](#data-pipeline)
  - [News Pipeline](#news-pipeline)
  - [Research Pipeline](#research-pipeline)
- [Data Formats](#data-formats)
- [Frontend](#frontend)
- [Configuration](#configuration)
- [CI/CD](#cicd)
- [Docker](#docker)
- [API Reference](#api-reference)
- [Constants Reference](#tuning-constants)
- [Troubleshooting](#troubleshooting)
- [Known Issues](#known-issues)
- [Security](#security)
- [License](#license)

---

## What It Does

| Capability | Detail |
| --- | --- |
| **News ingestion** | 50 tech sites, hybrid RSS + HTML scraping |
| **Research ingestion** | 8 academic APIs + 37 CSS-selector scrapers (IEEE, ACM, NeurIPS, arXiv, PubMed, …) |
| **Summarization** | `sshleifer/distilbart-cnn-6-6` locally (news) with `facebook/bart-large-cnn` fallback (research) — **no external LLM API** |
| **PDF resolution** | Unpaywall → arXiv → Semantic Scholar cascade to find open-access PDFs |
| **Retention** | News: 7 days. Research: 30 days. Automatic pruning. |
| **Frontend** | Static, zero-dependency, Memphis Design (1980s postmodern) |
| **Live refresh** | Browser polls RSS through CORS proxies every 5 minutes and merges into the static snapshot |
| **Hosting** | GitHub Pages, deployed by GitHub Actions via OIDC |
| **Refresh cadence** | `0 */6 * * *` (every 6 hours, UTC) |

**Hard constraints honoured:** no database, no backend server, no external CSS/JS frameworks, no CDNs, no emojis, no pure-white background.

---

## Architecture

```
┌─────────────────────── GitHub Actions (cron, every 6h) ───────────────────────┐
│                                                                               │
│  checkout → setup-python 3.11 → pip install → python main.py                   │
│                                                                               │
│  ┌── NEWS PIPELINE ──────────────┐   ┌── RESEARCH PIPELINE ──────────────────┐  │
│  │ load data/urls.json (50)      │   │ load data/research_sources.json      │  │
│  │ load data/rss.json   (37 live)│   │ 8 API fetchers ──┐                   │  │
│  │          ↓                    │   │ 37 CSS scrapers ─┤ ThreadPool(5)     │  │
│  │ RSS? → parse + meta desc     │   │  ↓ dedupe by id/title               │  │
│  │ else → HTML → extract links  │   │  ↓ batch_resolve_pdfs  (pool of 3)   │  │
│  │        → meta desc / DistilBART│  │  ↓ batch_summarize (DistilBART/BART) │  │
│  │ ThreadPool(5) across sources  │   │  ↓ sort by date, citations           │  │
│  └──────────────┬───────────────┘   └──────────────┬───────────────────────┘  │
│                 ↓                                   ↓                          │
│         data/summaries.json              data/papers-latest.json               │
│                                         data/papers-YYYY-MM-DD.json           │
│                 ↓                          ↓                                   │
│              purger()  (7d / 30d retention)                                   │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                ↓
              git add data/ → commit → push → upload-pages-artifact → deploy-pages
                                ↓
                    https://ujjwalsri2026.github.io/tech-news/
                                ↓
        ┌───────────────────────┴───────────────────────┐
        │  index.html  +  app.js  +  style.css          │
        │  fetches summaries.json / rss.json / papers   │
        │  + live RSS polling via 3 CORS proxies        │
        └───────────────────────────────────────────────┘
```

**Data flow is unidirectional and file-based:** Python writes JSON → git commits it → the browser reads it over plain HTTP. Nothing to scale, nothing to keep alive, nothing to pay for.

---

## Quick Start

### Prerequisites

- Python **3.11** (3.9+ should work)
- `git`
- ~**2 GB** free disk for Hugging Face model weights (cached in `~/.cache/huggingface`)
- Docker *(optional)*

### Local run

```bash
# 1. Clone
git clone https://github.com/ujjwalsri2026/tech-news.git
cd tech-news

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the full pipeline (news + research)
python main.py
```

The first run downloads the summarization models (~240 MB for DistilBART, ~1.6 GB for the BART fallback) and takes several minutes. Subsequent runs reuse the cache.

**Expected output:**

```
RSS feeds available for 37/50 sources
Loading summarization model...
[+] arxiv: 40 papers
[+] semantic_scholar: 25 papers
...
[+] Scrape sources: 87 papers
[+] After dedupe: 140 papers
[+] PDFs found: 62/140
[saver] Saved 140 papers to data/papers-2026-09-15.json
Done. 198 articles (150 RSS, 48 scraped) saved.
```

### View locally

Because `app.js` uses relative `fetch()` paths, you need a static file server (opening `index.html` via `file://` will trigger CORS errors in most browsers):

```bash
python -m http.server 8000
# then open http://localhost:8000
```

### Run only the news pipeline

The research pipeline is wrapped in a `try/except` (`main.py:135-148`), so it never blocks news. To skip it entirely, comment out the `run_aggregator(...)` call, or run the modules directly:

```python
from src.loader import load_urls
from src.scraper import parse_rss, extract_articles
from src.summarizer import preload
from src.saver import save
```

### Run only the research pipeline

```python
import json
from src.research.aggregator import run_aggregator
from src.research.saver import save_papers

config = json.load(open("data/research_sources.json"))
papers = run_aggregator(config, do_summarize=True)
save_papers(papers)
```

---

## Project Layout

```
.
├── .dockerignore                      # .git, .github, *.md
├── .github/
│   └── workflows/
│       └── scrape.yml                 # CI: scrape → commit → deploy to Pages
├── AGENT.md                           # Original build specification (historical)
├── Dockerfile                         # python:3.11-slim, runs main.py
├── docker-compose.yml                 # scraper service, ./data bind mount
├── README.md                          # This file
├── app.js                             # Frontend logic (375 lines, browser ES5 IIFE)
├── index.html                         # Static page shell (75 lines)
├── main.py                            # CLI entry point / orchestrator (152 lines)
├── requirements.txt                   # 6 unpinned Python dependencies
├── style.css                          # Memphis Design system (537 lines)
├── data/
│   ├── papers-latest.json             # ← generated (not yet committed)
│   ├── research_sources.json          # Research pipeline config
│   ├── rss.json                       # source name → RSS feed URL
│   ├── summaries.json                 # Latest news snapshot
│   └── urls.json                      # 50 news sources
└── src/
    ├── __init__.py
    ├── loader.py                      # Config + snapshot loaders
    ├── purger.py                      # Retention enforcement
    ├── saver.py                       # News JSON writer
    ├── scraper.py                     # News HTTP/RSS/HTML layer
    ├── summarizer.py                  # DistilBART (news)
    └── research/
        ├── __init__.py
        ├── aggregator.py              # Research orchestrator
        ├── api_sources.py             # 8 keyless academic APIs
        ├── loader.py                  # ⚠️ dead code (unused)
        ├── pdf_resolver.py            # Unpaywall/arXiv/S2 PDF cascade
        ├── saver.py                   # Papers JSON writer
        ├── scrape_sources.py          # 33-key CSS scraper registry
        └── summarizer.py              # DistilBART → BART-large-cnn
```

---

## Data Pipeline

### News Pipeline

**Source of truth:** `data/urls.json` (50 entries) and `data/rss.json` (50 keys, 37 with live feed URLs).

Each source is processed independently in a thread pool of 5 by `process_source()` (`main.py:26`):

**Path A — RSS (preferred when a feed exists and parses)**

1. `parse_rss(feed_url, max_items=10)` parses the feed with `feedparser`
2. For each of up to **10** entries, the article page is fetched
3. The `<meta name="description">` is extracted (`fetch_meta_description`, falling back to `og:description`)
4. Item is tagged `via: "rss"` → the frontend renders a pulsing **LIVE** badge

**Path B — HTML scrape (when RSS is missing or fails)**

1. Homepage HTML fetched via `fetch()` — direct `requests` GET, falling back to the Jina reader (`https://r.jina.ai/{url}`) on any exception
2. `extract_articles(html, base_url)` walks every `<a href>`, discarding:
   - non-HTTP schemes (`#`, `javascript:`, `mailto:`, `tel:`)
   - off-domain links
   - **11 path patterns**: `/tag/`, `/category/`, `/author/`, `/page/`, `/search`, `/tags/`, `/login`, `/signup`, `/about`, `/contact`, `/privacy`, `/terms`
   - duplicates
   - link text outside the **15–300 character** range
   - blacklisted labels: `home`, `menu`, `skip to content`, `read more`
   - preferring inner `h1`–`h4` text as the title
3. Capped at **5** articles per source
4. Each article gets its meta description; if absent, its full text (≤8000 chars) is summarized by `summarize_short()` (DistilBART, 15–80 tokens) — only when text exceeds 200 characters

If a source fails entirely, it emits `{"title": f"Failed to load {name}"}` so one bad site never kills the run.

Finally `save()` writes the payload to `data/summaries.json`, then triggers `purge()`. Each run overwrites the previous one; the news side keeps no dated snapshots.

### Research Pipeline

Orchestrated by `run_aggregator(config, do_summarize=True)` in `src/research/aggregator.py:35`, wrapped in a `try/except` so failures never affect the news pipeline.

**Stage 1 — API sources (8 configured, 9 implemented)**

| Source | Endpoint | Notes |
| --- | --- | --- |
| arXiv | `export.arxiv.org/api/query` | Atom XML; category `preprint`; always open access |
| Semantic Scholar | `api.semanticscholar.org/graph/v1/paper/search` | 1.1 s sleep to respect rate limits |
| OpenAlex | `api.openalex.org/works` | Polite pool via `mailto=` |
| Crossref | `api.crossref.org/works` | Polite pool; extracts venue + `is-referenced-by-count` |
| DBLP | `dblp.org/search/publ/api` | Picks `.pdf` from `ee` list; **no abstracts**; 0.5 s sleep |
| Papers with Code | `paperswithcode.com/api/v1/papers/` | category `benchmark` |
| OpenReview | `api2.openreview.net/notes` | Non-200 → skipped; 0.5 s sleep |
| PubMed | NCBI E-utilities `esearch` + `efetch` | XML; **no PDFs** |
| Zenodo | `zenodo.org/api/records` | Implemented but not in config (see [Known Issues](#known-issues)) |

Each fetcher is independently `try/except`-wrapped, logging `[+] name: N papers` or `[!] name: err`.

**Stage 2 — CSS-selector scrapers (37 configured, 33 registry keys)**

Ten generic fetchers — `fetch_ieee_xplore`, `fetch_acm_dl`, `fetch_google_scholar` (defaults to Jina), `fetch_nature_mi`, `fetch_jmlr`, `fetch_elsevier`, `fetch_springer`, `fetch_conference`, `fetch_tech_lab`, `fetch_arxiv_preprint` — are mapped by the `SCRAPERS` registry to 33 config keys. E.g. `ieee_tpami` and `ieee_tnnls` both → `fetch_ieee_xplore`; 13 conferences → `fetch_conference`; 4 Elsevier journals → `fetch_elsevier`.

Each scraper runs `soup.select(selector)[:20]` and takes the first `<a href>` from each node, absolutizing relative URLs. **These produce skeleton records** — empty `abstract`, `authors`, `published`, and `citations: 0`.

**Stage 3 — Deduplication**

`id`-based, then normalized-title-based (lowercased, whitespace-collapsed).

**Stage 4 — PDF resolution** (`batch_resolve_pdfs`, pool of 3)

For each paper, a 3-step cascade:
1. **Unpaywall** — `api.unpaywall.org/v2/{doi}` → `best_oa_location.url_for_pdf`
2. **arXiv** — `ti:{title}` query, first-50-char title match
3. **Semantic Scholar** — `openAccessPdf` (1.1 s sleep)

On success: `pdf_url` is set and `open_access = True`. The throttled pool of 3 is deliberate — it protects the free API rate limits.

**Stage 5 — Summarization** (`batch_summarize`)

DistilBART first (`num_beams=2`, `early_stopping`); on failure `facebook/bart-large-cnn`; on total failure the raw text is returned. Text under 100 characters passes through untouched. Papers with no summary fall back to `abstract[:200]`, then `"No abstract available."`.

**Stage 6 — Sort** by `(published[:10], citations)` descending — newest first, citations as tiebreaker.

### Retention

`src/purger.py` runs after every save and makes three passes:

| Pattern | Retention |
| --- | --- |
| `data/digest-*.json` | 7 days |
| `data/papers-????-??-??.json` | 30 days |

Malformed filenames are skipped rather than deleted. Note that `data/papers-latest.json` is a mirror and is **not** purged, and that `data/summaries.json` is **not** purged either — it is always overwritten in place by the next run.

---

## Data Formats

### `data/summaries.json`

```json
{
  "generated_at": "2026-09-15T11:32:36.045477+00:00",
  "source_count": 50,
  "article_count": 198,
  "items": [
    {
      "source": "Ars Technica",
      "type": "news",
      "title": "…",
      "url": "https://…",
      "description": "…"
    }
  ]
}
```

Current snapshot: **198 articles from all 50 sources**, 75 KB.

| `type` | count | | `type` | count |
| --- | --- | --- | --- | --- |
| news | 51 | | startups | 10 |
| blog | 39 | | community | 6 |
| enterprise | 26 | | ai | 6 |
| market | 23 | | hardware | 5 |
| research | 16 | | reviews | 5 |
| apple | 5 | | google | 5 |
| android | 1 | | | |

> **Note:** snapshot items currently lack `via` and `published`, so the LIVE badge never renders for static data and card timestamps fall back to `generated_at`. Live-polled RSS items do carry both.

### `data/rss.json`

Object mapping source name → feed URL. 50 keys, **37 non-empty**, 13 empty strings:

```
Medium, Hashnode, Substack, In Plain English, Bloomberg, CIO,
Washington Post, Reuters, FT, WSJ, Fortune, Business Insider, CB Insights
```

The 13 with empty feeds fall back to HTML scraping (Medium/Hashnode/Substack also set `use_jina: true` in `urls.json` because their homepages are JS-rendered).

### `data/urls.json`

Array of 50 objects:

```json
{ "name": "Ars Technica", "url": "https://arstechnica.com", "type": "news" }
{ "name": "Medium", "url": "https://medium.com", "type": "blog", "use_jina": true }
```

### `data/research_sources.json`

Two sections:

```jsonc
{
  "api_sources": {
    "arxiv": {
      "enabled": true,
      "categories": ["cs.AI", "cs.LG", "cs.CL"],
      "max_results": 40,
      "sort_by": "submittedDate"
    }
  },
  "scrape_sources": {
    "ieee_xplore": {
      "enabled": true,
      "url": "https://ieeexplore.ieee.org/",
      "selector": "a[href*='/document/']",
      "max_results": 20
    }
  }
}
```

### `data/papers-*.json` (research output)

```jsonc
{
  "id": "2409.12345",
  "title": "…",
  "abstract": "…",
  "authors": ["A. Author", "B. Author"],
  "published": "2024-09-20",
  "source": "arxiv",
  "category": "preprint",
  "url": "https://arxiv.org/abs/2409.12345",
  "pdf_url": "https://arxiv.org/pdf/2409.12345",
  "doi": "10.1145/…",
  "citations": 12,
  "venue": "NeurIPS",
  "open_access": true,
  "ai_summary": "…"
}
```

`save_papers()` writes the dated file first, then mirrors it to `data/papers-latest.json` (the file the frontend actually reads).

---

## Frontend

Three files, no build step, no framework, no CDN, no bundler. `app.js` is a vanilla ES5 async IIFE loaded by a plain `<script>` tag.

### `index.html`

- **Memphis decorations:** 13 inline SVGs (triangles, circles, zigzag polylines, cross, dot grid, squiggle, rotated square, dashed circle) in a fixed, `pointer-events: none` layer
- **Header:** `TECHPULSE` title, squiggle underline SVG, subtitle, mono timestamp
- **Tab bar:** `News` (active) and `Research`
- **Two panels:** `#filters` + `#cards` (news), `#research-section` + `#research-filters` + `#research-grid` (research, hidden)
- **Footer:** "Built with GitHub Actions + DistilBART" + 5 SVG shapes
- OG tags for social sharing; all asset paths relative so the site works at any Pages subpath

### `app.js`

| Concern | Detail |
| --- | --- |
| Bootstrap | `mergeAndRender()` → `pollRSS()` → `setInterval(pollRSS, 300000)` |
| Static data | Fetches `data/summaries.json`, `data/rss.json`, `data/papers-latest.json` |
| Live data | Batches feeds 10 at a time → `Promise.allSettled` → first 5 entries per feed |
| CORS proxies | Tried in order: `api.allorigins.win/raw?url=`, `corsproxy.io/?url=`, `api.codetabs.com/v1/proxy?quest=` |
| RSS parsing | `DOMParser` with `text/xml`; reads both `entry` (Atom) and `item` (RSS) |
| Merging | Dedupes by `url` across snapshot + live, snapshot first |
| Filtering | Pure CSS `display` toggle — no refetch, instant |
| Stagger | 30 ms per card `fadeInUp` |
| Security | `escapeHtml()` uses `textContent` → `innerHTML` to neutralize injected markup |
| Time | `relativeTime()` → `just now` / `Xm ago` / `Xh ago` / `Xd ago` |

Card anatomy: pulsing red `LIVE` badge (when `via === "rss"`), rotated `.type-badge`, dashed-underline `.source-tag`, 3-line clamped description, `Read more →` link, relative timestamp.

Research card anatomy: category filter pills with counts (`CAT (n)`), `.oa-badge` when a `pdf_url` exists, `.venue-tag`, `.citation-count`, first 3 authors + `et al.`, a `<details>` abstract toggle, an `.ai-summary` block, and a direct PDF link.

### `style.css`

A complete Memphis Design system in 537 lines.

**Palette (`:root`):**

| Variable | Value | Use |
| --- | --- | --- |
| `--memphis-pink` | `#FF71CE` | primary accent |
| `--memphis-yellow` | `#FFCE5C` | secondary accent |
| `--memphis-teal` | `#86CCCA` | secondary accent |
| `--memphis-purple` | `#6A7BB4` | tabs, active states |
| `--memphis-orange` | `#FF8A5C` | secondary accent |
| `--memphis-lime` | `#B8E994` | secondary accent |
| `--bg` | `#FDF6F0` | warm off-white (never `#FFF`) |
| `--surface` | `#FFF` | cards only |
| `--text` | `#2D2D2D` | body |
| `--text-muted` | `#6B6B6B` | metadata |
| `--border` | `#E8E0DA` | hairlines |

**Signature techniques:**
- Inline-SVG `background-image` data-URI at 4–6% opacity
- 12 `.deco-*` shapes with staggered `float` animation delays (±8 px)
- 2 px clashing card borders using `var(--card-color)`, assigned round-robin
- Rotated pills (`rotate(-1deg)` / `rotate(1deg)` alternating) and rotated type badges (`rotate(-3deg)`)
- Alternating card rotation via `:nth-child(odd/even/5n)`; hover resets to `translateY(-2px) rotate(0)`
- Squiggle SVG underline under the title
- `-webkit-line-clamp: 3` descriptions
- Responsive: mobile ≤768 px → 1 column + decorations hidden + rotation removed; tablet 769–1024 px → 2 columns; desktop ≥1025 px → 3 columns with `grid-auto-flow: dense`
- `@media print` — strips decorations/filters, single column, no rotation or shadow

**Keyframes:** `fadeInUp` (300 ms), `float` (±8 px), `pulse` (LIVE dot).

---

## Configuration

### Environment variables

**None.** The project reads no environment variables. There is no `.env`, no `OPENAI_API_KEY`, and no `env:` block in the workflow. Every outbound API used is keyless and free-tier.

### Tuning constants

All hardcoded — no config file. Change them at the locations below.

| Constant | Value | Location |
| --- | --- | --- |
| News thread pool | 5 workers | `main.py:120` |
| Scrape-source thread pool | 5 workers | `scrape_sources.py:233` |
| PDF resolve thread pool | 3 workers | `pdf_resolver.py:81` |
| Retry attempts | 3, exponential, max wait 10 s | `scraper.py:14` |
| Timeouts | 20 s (news HTML), 30 s (Jina / research), 15 s (RSS) | `scraper.py:16,26,55` |
| Max extracted text | 8000 chars | `scraper.py:8` |
| Max articles per source | 5 (scrape) / 10 (RSS) | `scraper.py:11,51` |
| News retention | 7 days | `purger.py:7` |
| Research retention | 30 days | `purger.py:8` |
| Client poll interval | 5 minutes | `app.js:16` |
| Cron schedule | `0 */6 * * *` | `.github/workflows/scrape.yml:5` |
| News model | `sshleifer/distilbart-cnn-6-6` | `src/summarizer.py:6` |
| Research models | `sshleifer/distilbart-cnn-6-6` → `facebook/bart-large-cnn` | `src/research/summarizer.py:15,26` |
| User agent | `Mozilla/5.0 (compatible; TechPulseBot/1.0)` | `scraper.py:7` |
| Polite-pool email | `techpulse@example.com` | `api_sources.py:118,154`, `pdf_resolver.py:8` |
| Semantic Scholar delay | 1.1 s | `api_sources.py:104`, `pdf_resolver.py:63` |

> Change `techpulse@example.com` to your real address — it is the contact sent in the polite-pool parameters for OpenAlex, Crossref, and Unpaywall.

### Adding a news source

1. Append to `data/urls.json`:
   ```json
   { "name": "Example Tech", "url": "https://example.com", "type": "news" }
   ```
2. Add the same `name` as a key to `data/rss.json` (feed URL, or `""` to force HTML scraping):
   ```json
   "Example Tech": "https://example.com/feed.xml"
   ```
3. Add a matching entry to the hardcoded `rssTypeMap` in `app.js:358` (used for the type badge on live-polled items)
4. Run `python main.py` and confirm the source appears in `summaries.json`

### Adding a research API source

Add a fetcher function to `src/research/api_sources.py` returning the normalized paper schema, register it in the `api_sources` dict in `src/research/aggregator.py:41-51`, then add its config block to `data/research_sources.json`.

### Adding a research scrape source

Add its config block to `data/research_sources.json` with a CSS `selector` targeting article links, then map its key to one of the 10 generic fetchers in the `SCRAPERS` registry at `scrape_sources.py:182-216`. A key with no registry entry silently returns `[]`.

---

## CI/CD

`.github/workflows/scrape.yml` — **"TechPulse Scrape & Deploy"**

**Triggers:** `schedule: "0 */6 * * *"` + `workflow_dispatch` (manual)
**Top-level permissions:** `contents: write`

### `build` job (ubuntu-latest)

1. `actions/checkout@v4` — `token: ${{ secrets.GITHUB_TOKEN }}`, `fetch-depth: 0` (full history, needed for rebase)
2. `actions/setup-python@v5` — Python 3.11
3. `pip install -r requirements.txt`
4. `python main.py` — runs both pipelines
5. **Commit results** — a deliberate rebase dance so a human push landing mid-run isn't clobbered:
   ```bash
   git config user.name "github-actions[bot]"
   git config user.email "github-actions[bot]@users.noreply.github.com"
   git stash
   git pull --rebase origin main
   git stash pop
   git add data/
   git diff --staged --quiet || git commit -m "TechPulse: $(date -u +%Y-%m-%d\ %H:%M)Z"
   git push
   ```
   The `git diff --staged --quiet ||` guard means a run that changed nothing produces no empty commit.
6. `actions/upload-pages-artifact@v5` with `path: .` — the repository root **is** the Pages artifact

### `deploy` job

`needs: build`; permissions `pages: write` + `id-token: write`; environment `github-pages`; single step `actions/deploy-pages@v5` (OIDC, no long-lived token).

### Required repository settings

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. **Settings → Actions → General → Workflow permissions: Read and write**
3. The repository name determines the URL: `https://<user>.github.io/tech-news/`

> A manual run from the Actions tab is the fastest way to verify the setup end to end.

---

## Docker

```yaml
# docker-compose.yml
services:
  scraper:
    build: .
    volumes:
      - ./data:/app/data
```

```bash
docker compose run --rm scraper          # one-shot scrape, results land in ./data
```

The `Dockerfile`:

```dockerfile
FROM python:3.11-slim
RUN apt-get install -y --no-install-recommends build-essential
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

This is a **batch job, not a service** — no `EXPOSE`, no `ports:`, no `restart` policy. The `./data` bind mount is what lets the container's output reach the repo for committing. Expect a large first build (PyTorch is ~800 MB of wheels) and a slow first run (model weights download inside the container unless you add a Hugging Face cache mount).

---

## API Reference

### External APIs consumed (all keyless)

**News:** 50 site homepages (`data/urls.json`) · 37 RSS feeds (`data/rss.json`) · Jina reader `https://r.jina.ai/{url}`

**Research:** `export.arxiv.org/api/query` · `api.semanticscholar.org/graph/v1/paper/search` · `api.openalex.org/works` · `api.crossref.org/works` · `dblp.org/search/publ/api` · `paperswithcode.com/api/v1/papers/` · `api2.openreview.net/notes` · `eutils.ncbi.nlm.nih.gov/entrez/eutils/{esearch,efetch}.fcgi` · `zenodo.org/api/records` · `api.unpaywall.org/v2/{doi}`

**Browser CORS proxies (tried in order):** `api.allorigins.win/raw?url=` · `corsproxy.io/?url=` · `api.codetabs.com/v1/proxy?quest=`

### Internal module API

```python
# src/loader.py
load_urls(path="data/urls.json") -> list[dict]
load_summaries(path="data/summaries.json") -> dict      # unused

# src/scraper.py
fetch_text(url) -> str                                   # retried 3x, ≤8000 chars
fetch_via_jina(url) -> str
fetch(url, use_jina=False) -> str                        # Jina fallback on any exception
fetch_raw(url, use_jina=False) -> str                    # raw HTML
parse_rss(feed_url, max_items=10) -> list[dict]          # [] on any failure
extract_articles(html, base_url) -> list[dict]           # max 5
fetch_meta_description(html) -> str

# src/summarizer.py
preload() -> None
summarize(text, source_type="news") -> str               # 30-150 tokens, unused
summarize_short(text) -> str                             # 15-80 tokens

# src/saver.py
save(results) -> None                                    # overwrites summaries.json

# src/purger.py
purge() -> None                                          # 7d news / 30d research

# src/research/aggregator.py
run_aggregator(config, do_summarize=True) -> list[dict]

# src/research/pdf_resolver.py
resolve_pdf(paper, email="techpulse@example.com") -> paper
batch_resolve_pdfs(papers) -> papers

# src/research/summarizer.py
summarize(text, max_length=80, min_length=25) -> str
batch_summarize(papers, ...) -> papers

# src/research/saver.py
save_papers(papers, path=None) -> str                    # dated file + papers-latest.json
```

### Normalized paper schema

Every research fetcher returns this shape, so the aggregator, PDF resolver, summarizer, and frontend can all assume it:

```
id, title, abstract, authors[], published, source, category,
url, pdf_url, doi, citations, venue, open_access
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'src'`**
Run from the repository root. `src/research/aggregator.py:8` inserts its parent into `sys.path`, so relative execution from another cwd can break imports.

**`ModuleNotFoundError: No module named 'research'`**
Same root cause — `main.py` relies on the aggregator's `sys.path` manipulation. Run from the repo root.

**Research tab is empty in the browser**
Expected until `data/papers-latest.json` exists. Check whether `python main.py` logged `[saver] Saved N papers to …`. The file has never been committed; see [Known Issues](#known-issues).

**First run hangs for minutes**
It is downloading model weights. Check `~/.cache/huggingface` for growth. Set `HF_HOME` to relocate the cache.

**`OSError: [Errno 122] Disk quota exceeded`**
Two model families ≈ 1.8 GB. Delete the cache and consider removing the BART fallback, or skip research entirely (it is already `try/except`-isolated).

**A source shows "Failed to load …"**
The site blocked the bot or changed markup. Add an RSS feed to `data/rss.json` — that path is far more reliable. For JS-rendered sites set `use_jina: true`.

**Live feed shows a CORS error in the console**
All three CORS proxies failed. Expected occasionally; the static snapshot still renders. The `LIVE` badge simply won't appear for that cycle.

**Docker build is slow / image is large**
`torch` is the bulk. `build-essential` is installed but unused — all six requirements ship prebuilt wheels. Removing it shrinks the image.

**CI run: permission denied on push**
Set **Settings → Actions → Workflow permissions** to *Read and write*.

**CI run: push rejected (non-fast-forward)**
A human pushed during the run. The rebase dance handles this; re-run the workflow.

**CI run: `pip install` times out**
There is no pip cache. `torch` downloads on every 6-hourly run. Add `cache: 'pip'` to `setup-python@v5`.

**Stale `data/digest-*.json` files accumulating**
Retention is 7 days. If older files linger, `purge()` is not being called — confirm `save()` reaches its final line and that filenames match `digest-YYYY-MM-DD.json`.

---

## Known Issues

Honest list of what does not currently work as intended:

1. **`data/papers-latest.json` has never been generated.** The file is absent from disk *and* from all git history, so the Research tab renders empty in production. `save_papers()` has apparently never completed a successful run in CI.
2. **`app.js:355` references `window.__urlsData`, which is never defined.** The live-RSS type lookup always falls through to the hardcoded 27-entry `rssTypeMap`.
3. **Snapshot items lack `via` and `published`.** The LIVE badge never renders for static data, and card timestamps always show `generated_at`.
4. **Four configured scrape sources are no-ops.** `zenodo`, `core`, `citeseerx`, and `cogprints` appear in `research_sources.json` but are missing from the `SCRAPERS` registry, so they silently return `[]`.
5. **Zenodo raises on every run.** It is in the aggregator's API registry but *not* in `api_sources` config, so `fetch_zenodo({})` raises `KeyError: 'max_results'` — caught and logged as `[!] zenodo: 'max_results'`.
6. **Dead code:** `src/research/loader.py` (never imported), `src/loader.py:load_summaries()` (never called), `src/summarizer.py:summarize()` (superseded by `summarize_short()`).
7. **The `deploy` job has no `actions/configure-pages@v5` step**, which normally precedes upload and deploy.
8. **`upload-pages-artifact` uses `path: .`** — the entire repo is published, including `Dockerfile`, `main.py`, and `src/`. Only `.git` is stripped.
9. **`summaries.json` is 75 KB**, exceeding the 50 KB budget stated in the original spec.
10. **No pip caching in CI** — `torch` reinstalls on every run.
11. **DBLP returns no abstracts** and PubMed returns no PDFs, so those papers fall back to "No abstract available."

### Divergences from `AGENT.md`

`AGENT.md` is the original build prompt. The implementation intentionally (and in some cases accidentally) diverges:

| Spec (`AGENT.md`) | Reality |
| --- | --- |
| `openai` + `gpt-4o-mini` summarization | Local `transformers` + `torch` (DistilBART / BART) — no API key, no cost |
| `OPENAI_API_KEY` secret in workflow | Removed entirely; no env vars at all |
| Payload key `count` | `source_count` + `article_count` |
| Repo named `techpulse` | Repo is `tech-news` |
| Specific 50-source list | Different 50 sources shipped in `data/urls.json` |
| No research pipeline | `src/research/` package, `data/research_sources.json`, `data/rss.json`, `Dockerfile`, and `docker-compose.yml` all added later |
| `summaries.json` < 50 KB | 75 KB |
| `README.md` in the tree | This file (written later) |

---

## Security

- **No credentials anywhere.** Zero environment variables, zero secrets, no `.env` file. Every external API is keyless and free-tier.
- **XSS defense in place.** `escapeHtml()` (`app.js:280`) uses the `textContent` → `innerHTML` trick to neutralize scraped markup before insertion.
- **No `innerHTML` with raw remote content** for any other field.
- **Relative asset paths** throughout, so the site works correctly at any Pages subpath.
- **A committed `GITHUB_TOKEN`** with `contents: write` is scoped to the single run. The `git diff --staged --quiet` guard means it cannot create empty commits.
- **Contact email is a placeholder.** `techpulse@example.com` is hardcoded in `api_sources.py:118,154` and `pdf_resolver.py:8`. Replace it with a monitored address — Unpaywall's polite pool and OpenAlex/Crossref etiquette both depend on it.
- **Polite-pool compliance is throttled, not enforced.** Semantic Scholar 1.1 s sleeps and a 3-worker PDF pool keep you inside free limits. If you raise `max_workers`, raise the delays too.
- **The published Pages artifact includes the full repo** (`path: .`). If you add anything sensitive, exclude it before deploying.

---

## Contributing

```bash
git checkout -b my-change
# ...edit...
python main.py                 # verify the pipeline still runs
git commit -am "describe your change"
git push origin my-change
```

Conventions worth matching: stdlib-first, no new dependencies without discussion, every network fetch wrapped in `try/except` so one failure cannot kill a run, and all new sources registered in **both** the Python config and `app.js`'s `rssTypeMap`.

## License

No license file is present. Add one (MIT is the usual choice for this kind of project) before publishing publicly.

---

<div align="center">

**TechPulse** — built with GitHub Actions + DistilBART

*No database. No server. No API keys. Just JSON files and a cron.*

</div>
