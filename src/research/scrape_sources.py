"""
Scrape-based research sources using text extraction.
Covers IEEE, ACM, Google Scholar, Nature MI, JMLR, all major conferences,
big tech labs, ScienceDirect journals, Springer.
"""
import time
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


def _get_text(url, use_jina=False):
    if use_jina:
        try:
            jina_url = f"https://r.jina.ai/{url}"
            r = requests.get(jina_url, headers={"Accept": "text/plain"}, timeout=30)
            r.raise_for_status()
            return r.text
        except Exception:
            pass
    try:
        r = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception:
        return None


def _extract_articles(html, selector, url_base):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for el in soup.select(selector)[:20]:
        a = el.find("a")
        if a and a.get("href"):
            href = a["href"]
            if not href.startswith("http"):
                href = f"{url_base.rstrip('/')}/{href.lstrip('/')}"
            title = a.get_text(strip=True)
            results.append({"title": title, "url": href})
    return results


def fetch_ieee_xplore(config):
    html = _get_text(config["url"], config.get("use_jina", False))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://ieeexplore.ieee.org")
    return [{
        "id": f"ieee:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "IEEE Xplore",
        "category": "index", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": "IEEE", "open_access": False,
    } for a in articles if a["title"]]


def fetch_acm_dl(config):
    html = _get_text(config["url"], config.get("use_jina", False))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://dl.acm.org")
    return [{
        "id": f"acm:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "ACM Digital Library",
        "category": "index", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": "ACM", "open_access": False,
    } for a in articles if a["title"]]


def fetch_google_scholar(config):
    html = _get_text(config["url"], config.get("use_jina", True))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://scholar.google.com")
    return [{
        "id": f"gs:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "Google Scholar",
        "category": "index", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": "Scholar", "open_access": False,
    } for a in articles if a["title"]]


def fetch_nature_mi(config):
    html = _get_text(config["url"], config.get("use_jina", False))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://www.nature.com")
    return [{
        "id": f"nature:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "Nature Machine Intelligence",
        "category": "journal", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": "Nature Machine Intelligence",
        "open_access": False,
    } for a in articles if a["title"]]


def fetch_jmlr(config):
    html = _get_text(config["url"], config.get("use_jina", False))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://www.jmlr.org")
    return [{
        "id": f"jmlr:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "JMLR",
        "category": "journal", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0,
        "venue": "Journal of Machine Learning Research", "open_access": True,
    } for a in articles if a["title"]]


def fetch_elsevier(config):
    html = _get_text(config["url"], config.get("use_jina", True))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://www.sciencedirect.com")
    name = config.get("name", "ScienceDirect")
    return [{
        "id": f"elsevier:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": name,
        "category": "journal", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": name, "open_access": False,
    } for a in articles if a["title"]]


def fetch_springer(config):
    html = _get_text(config["url"], config.get("use_jina", False))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://link.springer.com")
    name = config.get("name", "Springer")
    return [{
        "id": f"springer:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": name,
        "category": "journal", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": name, "open_access": False,
    } for a in articles if a["title"]]


def fetch_conference(config):
    html = _get_text(config["url"], config.get("use_jina", True))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], config["url"])
    name = config.get("name", "Conference")
    return [{
        "id": f"conf:{name}:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": name,
        "category": "conference", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": name, "open_access": False,
    } for a in articles if a["title"]]


def fetch_tech_lab(config):
    html = _get_text(config["url"], config.get("use_jina", True))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], config["url"])
    name = config.get("name", "Research Lab")
    return [{
        "id": f"lab:{name}:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": name,
        "category": "preprint", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": name, "open_access": True,
    } for a in articles if a["title"]]


def fetch_arxiv_preprint(config):
    html = _get_text(config["url"], config.get("use_jina", True))
    if not html:
        return []
    articles = _extract_articles(html, config["selector"], "https://www.techrxiv.org")
    return [{
        "id": f"techrxiv:{a['url']}", "title": a["title"], "abstract": "",
        "authors": [], "published": "", "source": "TechRxiv",
        "category": "preprint", "url": a["url"], "pdf_url": None,
        "doi": None, "citations": 0, "venue": "TechRxiv", "open_access": True,
    } for a in articles if a["title"]]


SCRAPERS = {
    "ieee_xplore": fetch_ieee_xplore,
    "acm_dl": fetch_acm_dl,
    "google_scholar": fetch_google_scholar,
    "nature_mi": fetch_nature_mi,
    "jmlr": fetch_jmlr,
    "ieee_tpami": fetch_ieee_xplore,
    "ieee_tnnls": fetch_ieee_xplore,
    "elsevier_ai": fetch_elsevier,
    "springer_ml": fetch_springer,
    "expert_systems": fetch_elsevier,
    "neural_networks": fetch_elsevier,
    "knowledge_based": fetch_elsevier,
    "applied_soft": fetch_elsevier,
    "neurips": fetch_conference,
    "icml": fetch_conference,
    "iclr": fetch_conference,
    "aaai": fetch_conference,
    "cvpr": fetch_conference,
    "iccv": fetch_conference,
    "eccv": fetch_conference,
    "acl": fetch_conference,
    "icse": fetch_conference,
    "fse": fetch_conference,
    "ase": fetch_conference,
    "issta": fetch_conference,
    "jair": fetch_conference,
    "google_research": fetch_tech_lab,
    "openai_research": fetch_tech_lab,
    "microsoft_research": fetch_tech_lab,
    "meta_ai": fetch_tech_lab,
    "techrxiv": fetch_arxiv_preprint,
    "automated_se": fetch_springer,
    "info_software_tech": fetch_elsevier,
}


def run_all_scrape_sources(config):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    all_papers = []
    sources = {k: v for k, v in config.items() if v.get("enabled", True)}

    def _fetch_one(name, src_cfg):
        fetch_fn = SCRAPERS.get(name)
        if not fetch_fn:
            return []
        try:
            return fetch_fn(src_cfg)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_one, k, v): k for k, v in sources.items()}
        for future in as_completed(futures):
            try:
                papers = future.result()
                all_papers.extend(papers)
            except Exception:
                pass

    return all_papers