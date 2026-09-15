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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
def fetch_text(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text[:MAX_CHARS]


def fetch_via_jina(url: str) -> str:
    resp = requests.get(f"https://r.jina.ai/{url}", timeout=30)
    resp.raise_for_status()
    return resp.text[:MAX_CHARS]


def fetch(url: str, use_jina: bool = False) -> str:
    if use_jina:
        return fetch_via_jina(url)
    try:
        return fetch_text(url)
    except Exception:
        return fetch_via_jina(url)


def fetch_raw(url: str, use_jina: bool = False) -> str:
    if use_jina:
        return fetch_via_jina(url)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return fetch_via_jina(url)


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


def extract_articles(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    articles = []
    seen_urls = set()
    parsed_base = urlparse(base_url)

    for a in soup.find_all("a", href=True):
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
        if href in seen_urls:
            continue

        title_el = a.find(["h1", "h2", "h3", "h4"])
        if title_el:
            title = title_el.get_text(strip=True)
        else:
            title = a.get_text(strip=True)

        if not title or len(title) < 15 or len(title) > 300:
            continue
        if title.lower() in ("home", "menu", "skip to content", "read more"):
            continue

        seen_urls.add(href)
        articles.append({"title": title, "url": href})

    return articles[:MAX_ARTICLES]


def fetch_meta_description(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    meta = soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return ""
