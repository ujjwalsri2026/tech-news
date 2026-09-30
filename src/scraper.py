import feedparser
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import urlparse

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechPulseBot/1.0)"}
MAX_CHARS = 8000
STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside"]
SKIP_PATHS = ["/tag/", "/category/", "/author/", "/page/", "/search", "/tags/", "/login", "/signup", "/about", "/contact", "/privacy", "/terms"]
MAX_ARTICLES = 5
LOGIN_WALL_TITLES = ("login", "log in", "sign in", "web login service", "access denied")
LOGIN_WALL_BODY = ("log in", "login", "password", "shibboleth", "account")
NAV_LABELS = (
    "home", "menu", "skip to content", "read more",
    "subscribe", "sign up", "sign in", "log in", "search",
    "next", "previous", "prev", "back", "share", "follow us",
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def fetch_text(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text[:MAX_CHARS]


JINA_BASE = "https://r.jina.ai/"


def fetch_via_jina(url: str) -> str:
    resp = requests.get(f"{JINA_BASE}{url}", timeout=30)
    resp.raise_for_status()
    return resp.text[:MAX_CHARS]


def fetch_raw_via_jina(url: str) -> str:
    """Jina reader output as HTML.

    The reader returns markdown by default, which carries no ``<a href>`` tags
    and no ``<meta>`` elements -- so link extraction and meta descriptions both
    come back empty. ``X-Return-Format: html`` returns the rendered DOM instead.
    Not truncated: cutting HTML mid-tag corrupts the parse.
    """
    resp = requests.get(
        f"{JINA_BASE}{url}",
        headers={"X-Return-Format": "html"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def fetch(url: str, use_jina: bool = False) -> str:
    if use_jina:
        return fetch_via_jina(url)
    try:
        return fetch_text(url)
    except Exception:
        return fetch_via_jina(url)


def fetch_raw(url: str, use_jina: bool = False) -> str:
    if use_jina:
        return fetch_raw_via_jina(url)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return fetch_raw_via_jina(url)


def parse_rss(feed_url: str, max_items: int = 10) -> list[dict]:
    if not feed_url:
        return []
    try:
        resp = requests.get(feed_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        items = []
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            published = entry.get("published", entry.get("updated", ""))
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "published": published,
                })
        return items
    except Exception:
        return []


NAV_LABELS = (
    "home", "menu", "skip to content", "read more",
    "subscribe", "sign up", "sign in", "log in", "log out",
    "search", "next", "previous", "prev", "back", "share",
    "follow us", "contact us", "about us", "privacy", "terms",
)


def is_login_wall(html: str) -> bool:
    """True when a fetch landed on an auth page instead of the real content.

    Some institutional sites (e.g. bu.edu from a datacenter IP) answer 200 with
    a Shibboleth login form. Without this check the extractor happily scrapes the
    form's own links -- "Get help logging in." -- and publishes them as articles.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return False
    title_el = soup.find("title")
    title = (title_el.get_text(strip=True).lower() if title_el else "")
    if not any(m in title for m in LOGIN_WALL_TITLES):
        return False
    body = soup.get_text(" ", strip=True)[:1500].lower()
    return sum(1 for m in LOGIN_WALL_BODY if m in body) >= 2


def _ssr_json_articles(html: str, base_url: str, path_prefix: str) -> list[dict]:
    """Recover articles from a client-rendered site's embedded SSR JSON payload.

    SvelteKit/Remix/Next-style SPAs render the body in JS, so the served HTML
    has zero <a> tags -- but they inline their initial data as a
    ``<script type="application/json">`` island. Reading that gives us titles,
    URLs and publish dates without a headless browser.
    """
    import json

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    articles = []
    for script in soup.find_all("script", attrs={"type": "application/json"}):
        try:
            data = json.loads(script.string or "{}")
        except Exception:
            continue

        def walk(node):
            if isinstance(node, dict):
                slug = node.get("slug")
                title = node.get("name") or node.get("title")
                if slug and title and node.get("page_type", "blog") == "blog":
                    articles.append({
                        "title": str(title).strip(),
                        "url": f"{base_url.rstrip('/')}{path_prefix}{slug}",
                    })
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)

    seen, unique = set(), []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    return unique[:MAX_ARTICLES]


def _is_nav(title: str) -> bool:
    t = title.lower().strip()
    return t in NAV_LABELS or any(t.startswith(x + " ") or t == x for x in NAV_LABELS)


def _scan_links(scope, parsed_base: str, seen: set) -> list[dict]:
    """Collect every plausible link, then rank.

    Ranking rather than truncating matters: real article links are often
    preceded in document order by a dozen nav links, so taking the first N
    would fill the card with chrome. Ranking the same candidate pool cannot
    reduce how many links we return, only improve which ones.
    """
    candidates = []
    for a in scope.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href in ("#", "javascript:void(0)", "/"):
            continue
        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue

        if href.startswith("/"):
            href = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
        elif not href.startswith("http"):
            continue

        parsed_href = urlparse(href)
        if parsed_href.netloc != parsed_base.netloc:
            continue

        path_lower = parsed_href.path.lower()
        if any(x in path_lower for x in SKIP_PATHS):
            continue
        if href in seen:
            continue

        title_el = a.find(["h1", "h2", "h3", "h4"])
        has_heading = title_el is not None
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)

        if not title or len(title) < 15 or len(title) > 300:
            continue

        seen.add(href)
        depth = len([p for p in parsed_href.path.split("/") if p])
        candidates.append((_is_nav(title), not has_heading, -depth, title, href))

    candidates.sort(key=lambda c: c[:3])
    return [{"title": t, "url": u} for _, _, _, t, u in candidates[:MAX_ARTICLES]]


def extract_articles(html: str, base_url: str, path_prefix: str = "") -> list[dict]:
    if is_login_wall(html):
        return []
    soup = BeautifulSoup(html, "html.parser")
    articles = _scan_links(soup, urlparse(base_url), set())
    if articles or not path_prefix:
        return articles
    # Zero <a> tags means the body is client-rendered -- fall back to SSR JSON.
    return _ssr_json_articles(html, base_url, path_prefix)


def fetch_meta_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""
