import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechPulseBot/1.0)"}
MAX_CHARS = 8000
STRIP_TAGS = ["script", "style", "nav", "footer", "header", "aside"]


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
