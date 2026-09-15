Here's your **complete, copy-paste-ready prompt**:

---

```markdown
# PROMPT: Build "TechPulse" — A Static Tech News Digest App

## OVERVIEW

Build a complete, production-ready web application called **TechPulse** that:
- Scrapes 50 tech news/market websites
- Uses an LLM API to generate 2–3 line summaries of each site's latest content
- Stores ALL data in JSON files (NO database)
- Retains ONLY the last 7 days of summaries (auto-purge older files)
- Is hosted entirely on **GitHub Pages** (zero backend, zero server)
- Uses **GitHub Actions** as the scheduled "backend" (cron every 6 hours)
- Features a **Memphis Design** UI (1980s postmodern: bold clashing colors, geometric shapes, squiggles, zigzags, abstract patterns, asymmetric layouts)

---

## ARCHITECTURE

```
techpulse/
├── .github/
│   └── workflows/
│       └── scrape.yml          # GitHub Actions: scrape → summarize → commit → deploy
├── src/
│   ├── __init__.py
│   ├── scraper.py              # Fetch + extract text (requests + BeautifulSoup + Jina fallback)
│   ├── summarizer.py           # LLM call (OpenAI gpt-4o-mini)
│   ├── saver.py                # Write JSON + auto-purge files older than 7 days
│   ├── loader.py               # Load URLs + summaries from disk
│   └── purger.py               # Delete data/history/*.json older than 7 days
├── data/
│   ├── urls.json               # 50 source definitions
│   ├── summaries.json          # Latest run output (served to frontend)
│   └── history/                # One file per day: YYYY-MM-DD.json (max 7 files)
├── main.py                     # Orchestrator (ThreadPoolExecutor, 5 workers)
├── requirements.txt
├── index.html                  # Frontend (Memphis Design)
├── app.js                      # Fetch + render logic
├── style.css                   # Memphis Design system
└── README.md
```

---

## DATA SOURCES (data/urls.json)

Include EXACTLY these 50 sources, each with `name`, `url`, `type`, and optional `use_jina` (true for JS-heavy/SPA sites):

```json
[
  {"name": "TechCrunch", "url": "https://techcrunch.com", "type": "startups"},
  {"name": "The Verge", "url": "https://www.theverge.com", "type": "news"},
  {"name": "WIRED", "url": "https://www.wired.com", "type": "news"},
  {"name": "Ars Technica", "url": "https://arstechnica.com", "type": "news"},
  {"name": "VentureBeat", "url": "https://venturebeat.com", "type": "ai"},
  {"name": "CNET", "url": "https://www.cnet.com", "type": "news"},
  {"name": "Engadget", "url": "https://www.engadget.com", "type": "news"},
  {"name": "ZDNet", "url": "https://www.zdnet.com", "type": "enterprise"},
  {"name": "TechRadar", "url": "https://www.techradar.com", "type": "news"},
  {"name": "Digital Trends", "url": "https://www.digitaltrends.com", "type": "news"},
  {"name": "Tom's Hardware", "url": "https://www.tomshardware.com", "type": "hardware"},
  {"name": "Tom's Guide", "url": "https://www.tomsguide.com", "type": "reviews"},
  {"name": "PCMag", "url": "https://www.pcmag.com", "type": "reviews"},
  {"name": "Slashdot", "url": "https://slashdot.org", "type": "community"},
  {"name": "Hacker News", "url": "https://news.ycombinator.com", "type": "community"},
  {"name": "9to5Mac", "url": "https://9to5mac.com", "type": "apple"},
  {"name": "9to5Google", "url": "https://9to5google.com", "type": "google"},
  {"name": "Android Authority", "url": "https://www.androidauthority.com", "type": "android"},
  {"name": "Gizmodo", "url": "https://gizmodo.com", "type": "news"},
  {"name": "Mashable", "url": "https://mashable.com", "type": "news"},
  {"name": "The Next Web", "url": "https://thenextweb.com", "type": "startups"},
  {"name": "MIT Technology Review", "url": "https://www.technologyreview.com", "type": "research"},
  {"name": "Bloomberg Technology", "url": "https://www.bloomberg.com/technology", "type": "market"},
  {"name": "Futurism", "url": "https://futurism.com", "type": "news"},
  {"name": "TechSpot", "url": "https://www.techspot.com", "type": "news"},
  {"name": "ReadWrite", "url": "https://readwrite.com", "type": "news"},
  {"name": "GigaOM", "url": "https://gigaom.com", "type": "enterprise"},
  {"name": "The Register", "url": "https://www.theregister.com", "type": "news"},
  {"name": "CIO", "url": "https://www.cio.com", "type": "enterprise"},
  {"name": "InfoWorld", "url": "https://www.infoworld.com", "type": "enterprise"},
  {"name": "Computerworld", "url": "https://www.computerworld.com", "type": "enterprise"},
  {"name": "Network World", "url": "https://www.networkworld.com", "type": "enterprise"},
  {"name": "TechRepublic", "url": "https://www.techrepublic.com", "type": "enterprise"},
  {"name": "PCWorld", "url": "https://www.pcworld.com", "type": "news"},
  {"name": "Lifehacker", "url": "https://lifehacker.com", "type": "news"},
  {"name": "MacRumors", "url": "https://www.macrumors.com", "type": "apple"},
  {"name": "Droid Life", "url": "https://www.droid-life.com", "type": "android"},
  {"name": "404 Media", "url": "https://www.404media.co", "type": "investigative"},
  {"name": "CB Insights", "url": "https://www.cbinsights.com", "type": "market"},
  {"name": "Tech in Asia", "url": "https://techinasia.com", "type": "startups"},
  {"name": "Silicon Republic", "url": "https://www.siliconrepublic.com", "type": "startups"},
  {"name": "NYT Technology", "url": "https://www.nytimes.com/section/technology", "type": "news"},
  {"name": "Washington Post Tech", "url": "https://www.washingtonpost.com/business/technology/", "type": "news"},
  {"name": "Reuters Technology", "url": "https://www.reuters.com/technology/", "type": "market"},
  {"name": "Financial Times Tech", "url": "https://www.ft.com/technology", "type": "market"},
  {"name": "WSJ Technology", "url": "https://www.wsj.com/tech", "type": "market"},
  {"name": "Fortune Tech", "url": "https://fortune.com/section/tech/", "type": "market"},
  {"name": "Business Insider Tech", "url": "https://www.businessinsider.com/technology", "type": "market"},
  {"name": "The Information", "url": "https://www.theinformation.com", "type": "market"},
  {"name": "arXiv CS", "url": "https://arxiv.org/list/cs/recent", "type": "research"},
  {"name": "Nature Technology", "url": "https://www.nature.com/sections/tech-policy", "type": "research"}
]
```

**Type categories:** `startups`, `news`, `ai`, `enterprise`, `hardware`, `reviews`, `community`, `apple`, `google`, `android`, `market`, `research`, `investigative`

---

## BACKEND (Python — runs in GitHub Actions)

### `requirements.txt`
```
requests
beautifulsoup4
openai
tenacity
```

### `src/scraper.py`
- `fetch_text(url)` → GET with `User-Agent: Mozilla/5.0 (compatible; TechPulseBot/1.0)`, timeout 20s, strip `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, return first 8000 chars of clean text
- `fetch_via_jina(url)` → GET `https://r.jina.ai/{url}`, timeout 30s, return first 8000 chars
- `fetch(url, use_jina=False)` → try `fetch_text` first, fall back to `fetch_via_jina` on any exception
- Decorate `fetch_text` with `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))`

### `src/summarizer.py`
- Singleton `OpenAI` client using `os.environ["OPENAI_API_KEY"]`
- `summarize(text, source_type)` → model `gpt-4o-mini`, `max_tokens=150`, `temperature=0.3`
- System prompt varies by `source_type`:
  - `market` / `startups`: "Summarize this business/tech market update in 2-3 lines. Mention companies, funding, or product moves."
  - `research`: "Summarize this research paper in 2-3 lines. State the key finding and its significance."
  - `ai`: "Summarize this AI/ML update in 2-3 lines. Name the model, company, or breakthrough."
  - default: "Summarize this article in 2-3 lines. Be factual and concise."

### `src/saver.py`
- `save(results)` → writes `data/summaries.json` with structure:
  ```json
  {
    "generated_at": "ISO-8601 UTC",
    "count": 50,
    "items": [
      {"source": "TechCrunch", "url": "...", "type": "startups", "summary": "..."}
    ]
  }
  ```
- Also writes `data/history/YYYY-MM-DD.json` (same structure)
- Calls `purger.purge()` after saving

### `src/purger.py`
- `purge()` → scan `data/history/`, delete any `.json` file whose filename date is older than 7 days from today (UTC)
- Log each deleted file

### `src/loader.py`
- `load_urls(path="data/urls.json")` → list of dicts
- `load_summaries(path="data/summaries.json")` → dict (return empty default if file missing)

### `main.py`
- Load URLs → `ThreadPoolExecutor(max_workers=5)` → for each source: `fetch()` → `summarize()` → collect result dict
- On exception per source: store `{"source": name, "url": url, "type": type, "summary": "⚠️ Failed: {error}"}`
- Call `save(results)`
- Print summary: `Done. {n}/50 entries saved.`

### `.github/workflows/scrape.yml`
```yaml
name: TechPulse Scrape & Deploy

on:
  schedule:
    - cron: "0 */6 * * *"
  workflow_dispatch: {}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt

      - name: Run scraper
        run: python main.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Commit results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/
          git diff --staged --quiet || git commit -m "TechPulse: $(date -u +%Y-%m-%d\ %H:%M)Z"
          git push

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: .

  deploy:
    needs: build
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## FRONTEND (Memphis Design)

### DESIGN SYSTEM — Memphis Style

**Color Palette (CSS variables):**
```css
:root {
  --memphis-pink: #FF71CE;
  --memphis-yellow: #FFCE5C;
  --memphis-teal: #86CCCA;
  --memphis-purple: #6A7BB4;
  --memphis-orange: #FF8A5C;
  --memphis-lime: #B8E994;
  --bg: #FDF6F0;
  --surface: #FFFFFF;
  --text: #2D2D2D;
  --text-muted: #6B6B6B;
  --border: #E8E0DA;
}
```

**Typography:**
- Headings: `system-ui`, weight 900, tight tracking (`letter-spacing: -0.02em`)
- Body: `system-ui`, weight 400, 1rem / 1.6
- Labels/tags: `system-ui`, 0.7rem, weight 600, uppercase, `letter-spacing: 0.05em`
- Monospace (metadata): `JetBrains Mono`, 0.8rem

**Memphis Visual Elements (MANDATORY):**
1. **Background pattern:** Subtle repeating geometric pattern (small triangles, dots, crosses) at 4–6% opacity using CSS `background-image` with inline SVG data URI
2. **Decorative shapes:** Floating geometric elements (circles, triangles, squiggles, zigzag lines) positioned absolutely around the page. Use CSS `clip-path: polygon()`, `border-radius`, and `transform: rotate()`. At least 8–12 decorative shapes visible at any viewport.
3. **Card borders:** 2px solid borders in clashing Memphis colors (alternate pink/teal/yellow/purple per card). Slight `transform: rotate(-0.5deg)` or `rotate(0.5deg)` on alternating cards for asymmetry.
4. **Type tags:** Small pill-shaped badges with Memphis colors, slightly rotated (`transform: rotate(-3deg)`), positioned top-right of each card
5. **Section dividers:** Zigzag or wavy SVG dividers between sections (inline SVG, 20px tall)
6. **Squiggle underlines:** Decorative SVG squiggles under the main title
7. **Dotted/dashed borders:** Use `border-style: dashed` or `dotted` on some elements
8. **Asymmetric layout:** Cards in a CSS Grid with `grid-template-columns: repeat(auto-fill, minmax(320px, 1fr))` but with varied card heights and slight rotations. NOT a perfect grid.
9. **No pure white background** — use `--bg: #FDF6F0` (warm off-white)
10. **No emojis** — use inline SVG icons (geometric/abstract style)

**Layout Structure:**
```
┌─────────────────────────────────────────────────┐
│  HEADER                                         │
│  "TECHPULSE" (huge, weight 900, with squiggle) │
│  Subtitle: "50 sources · 7 days · zero noise"  │
│  Last updated timestamp (monospace, small)      │
│  [Decorative: floating triangle top-right,      │
│   circle bottom-left, zigzag line]              │
├─────────────────────────────────────────────────┤
│  FILTER BAR                                     │
│  [All] [Startups] [AI] [Market] [Hardware]      │
│  [Enterprise] [Research] [Apple] [Android]      │
│  (Pill buttons, Memphis colors, active = filled)│
├─────────────────────────────────────────────────┤
│  CARDS GRID (asymmetric, varied rotations)      │
│  ┌──────────┐  ┌──────────────┐                 │
│  │ Card 1   │  │ Card 2       │                 │
│  │ (pink)   │  │ (teal)       │                 │
│  └──────────┘  └──────────────┘                 │
│  ┌──────────────┐  ┌──────────┐                 │
│  │ Card 3       │  │ Card 4   │                 │
│  │ (yellow)     │  │ (purple) │                 │
│  └──────────────┘  └──────────┘                 │
│  ... (50 cards total)                           │
├─────────────────────────────────────────────────┤
│  FOOTER                                         │
│  "Built with GitHub Actions + GPT-4o-mini"      │
│  [Decorative: row of small geometric shapes]    │
└─────────────────────────────────────────────────┘
```

**Card Structure:**
```html
<div class="card" style="--card-color: var(--memphis-pink)">
  <span class="type-badge">MARKET</span>
  <h3>Bloomberg Technology</h3>
  <p class="summary">Nvidia's data center revenue surged 220% YoY...</p>
  <a href="..." target="_blank" rel="noopener">Read original →</a>
  <time datetime="...">2h ago</time>
</div>
```

**Interactions:**
- Card hover: `transform: translateY(-3px) rotate(0deg)` + shadow increase, 200ms ease-out
- Filter pills: active = filled background + white text; inactive = outline
- Staggered entry animation: cards fade in + translate-Y(16px → 0), 80ms stagger
- Smooth scroll, no page transitions needed (single page)

**Responsive:**
- Mobile (< 768px): single column, decorative shapes reduced to 4–5, cards no rotation
- Tablet (768–1024px): 2 columns
- Desktop (> 1024px): 3 columns (asymmetric via `grid-auto-flow: dense` or manual spans)

### `app.js` Logic
1. `fetch("data/summaries.json")` → parse
2. Render timestamp
3. Build filter pills dynamically from unique `type` values
4. Render all cards (staggered animation via `animation-delay: ${index * 80}ms`)
5. Filter: clicking a pill hides non-matching cards (CSS class toggle, no re-fetch)
6. "Read original" links open in new tab
7. Relative time display: "2h ago", "1d ago" based on `generated_at`

### `index.html`
- Semantic HTML5
- Meta: charset, viewport, title "TechPulse — Tech News in 2-3 Lines", description, Open Graph
- Link to `style.css`, script `app.js` at end of body
- Inline SVG decorative shapes in a `<div class="decorations">` layer (position: fixed, pointer-events: none, z-index: -1)

### `style.css`
- CSS custom properties for all Memphis colors
- CSS Grid for card layout
- Inline SVG background pattern (data URI) for body
- Keyframe animations: `fadeInUp` for cards, `float` for decorative shapes (subtle 3s ease-in-out infinite)
- Print styles: hide decorations, single column
- No external dependencies (no Tailwind, no Bootstrap, no framework)

---

## 7-DAY RETENTION LOGIC

In `src/purger.py`:
```python
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

HISTORY_DIR = Path("data/history")
RETENTION_DAYS = 7

def purge():
    if not HISTORY_DIR.exists():
        return
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    for f in HISTORY_DIR.glob("*.json"):
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff:
                f.unlink()
                print(f"Purged: {f.name}")
        except ValueError:
            f.unlink()  # Malformed filename, delete
```

This runs automatically after every `save()`. The `data/history/` folder will NEVER contain more than 8 files (today + 7 previous days).

---

## DEPLOYMENT CHECKLIST

1. Create GitHub repo `techpulse`
2. Push all files
3. Settings → Secrets → Actions → add `OPENAI_API_KEY`
4. Settings → Pages → Source: **GitHub Actions**
5. Settings → Actions → General → Allow all actions (or "Read and write")
6. Trigger first run manually (Actions tab → "Scrape & Deploy" → "Run workflow")
7. After ~3 min, site is live at `https://<username>.github.io/techpulse/`

---

## CONSTRAINTS & RULES

- **NO database** — all persistence is JSON files on disk
- **NO backend server** — GitHub Actions is the only "compute"
- **NO external CSS/JS frameworks** — pure vanilla HTML/CSS/JS
- **NO emojis in UI** — use inline SVG geometric icons only
- **NO pure white (#FFF) backgrounds** — use `--bg: #FDF6F0`
- **NO 3-equal-column layouts** — asymmetric grid only
- **NO center-aligned hero** — offset, asymmetric composition
- **LLM model:** `gpt-4o-mini` (cost: ~$0.01 per run of 50 sources)
- **Concurrency:** 5 workers max (respects API rate limits)
- **Timeout:** 20s per fetch, 30s for Jina
- **Error handling:** Never crash the whole run; individual source failures are logged in the summary as "⚠️ Failed: {error}"
- **Git:** Only commit if `data/` actually changed (avoid empty commits)
- **File size:** `summaries.json` should stay under 50KB (50 × ~1KB per entry)

---

## DELIVERABLE

Generate ALL files listed in the file tree above, complete and production-ready. Each file must be self-contained and runnable. The frontend must look unmistakably like **Memphis Design** — bold, geometric, playful, 1980s postmodern. The backend must be clean, modular Python. The workflow must deploy to GitHub Pages on every run.
```

---

**How to use this prompt:**
- Paste it into Cursor / Windsurf / Claude / Copilot Workspace — it will generate every file
- Or use it as a human spec and build manually
- The `urls.json` is already populated with 50 real, active tech/market sites
- The Memphis design section is detailed enough that any AI or designer will produce the correct aesthetic (clashing pastels, geometric confetti, squiggles, asymmetric grid, no minimalism)

