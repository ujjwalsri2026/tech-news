"""
All free-API research sources. No keys needed.
Each function returns list[dict] with standardized paper format.
"""
import requests
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta, timezone


# ─── STANDARD PAPER FORMAT ───
# {
#   "id": str,           # unique identifier (source:id)
#   "title": str,
#   "abstract": str,
#   "authors": list[str],
#   "published": str,    # ISO date or "YYYY-MM-DD"
#   "source": str,       # display name
#   "category": str,     # which category bucket
#   "url": str,          # landing page
#   "pdf_url": str|None, # direct PDF (if available)
#   "doi": str|None,
#   "citations": int,
#   "venue": str,
#   "open_access": bool
# }


def fetch_arxiv(config: dict) -> list[dict]:
    """arXiv API — no key, no rate limit for reasonable use."""
    cats = " OR ".join(f"cat:{c}" for c in config["categories"])
    params = {
        "search_query": f"({cats})",
        "start": 0,
        "max_results": config["max_results"],
        "sortBy": config["sort_by"],
        "sortOrder": "descending",
    }
    resp = requests.get("http://export.arxiv.org/api/query", params=params, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []

    for entry in root.findall("atom:entry", ns):
        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
        title = " ".join(entry.find("atom:title", ns).text.split())
        abstract = " ".join(entry.find("atom:summary", ns).text.split())
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        published = entry.find("atom:published", ns).text[:10]
        categories = [c.get("term") for c in entry.findall("atom:category", ns)]

        papers.append({
            "id": f"arxiv:{arxiv_id}",
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published,
            "source": "arXiv",
            "category": "preprint",
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            "doi": None,
            "citations": 0,
            "venue": "arXiv preprint",
            "open_access": True,
        })
    return papers


def fetch_semantic_scholar(config: dict) -> list[dict]:
    """Semantic Scholar Graph API — no key, 1 req/sec."""
    papers = []
    for query in config["queries"]:
        params = {
            "query": query,
            "limit": config["max_results_per_query"],
            "fields": config["fields"],
            "sort": "publicationDate:desc",
        }
        resp = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
                            params=params, timeout=30)
        resp.raise_for_status()
        for p in resp.json().get("data", []):
            ext = p.get("externalIds", {})
            doi = ext.get("DOI")
            oa_pdf = (p.get("openAccessPdf") or {}).get("url")
            papers.append({
                "id": f"s2:{p.get('paperId', '')}",
                "title": p.get("title", ""),
                "abstract": p.get("abstract") or "",
                "authors": [a["name"] for a in (p.get("authors") or [])],
                "published": p.get("publicationDate") or str(p.get("year", "")),
                "source": "Semantic Scholar",
                "category": "index",
                "url": p.get("url", ""),
                "pdf_url": oa_pdf,
                "doi": doi,
                "citations": p.get("citationCount", 0),
                "venue": p.get("venue") or "Unknown",
                "open_access": oa_pdf is not None,
            })
        time.sleep(1.1)  # respect rate limit
    return papers


def fetch_openalex(config: dict) -> list[dict]:
    """OpenAlex API — no key, 10 req/sec."""
    from_date = (datetime.now(timezone.utc) - timedelta(days=config["from_date_days_ago"])).strftime("%Y-%m-%d")
    papers = []
    for term in config["search_terms"]:
        params = {
            "filter": f"from_publication_date:{from_date},type:article",
            "search": term,
            "per-page": config["max_results_per_term"],
            "sort": "publication_date:desc",
            "mailto": "techpulse@example.com",
        }
        resp = requests.get("https://api.openalex.org/works", params=params, timeout=30)
        resp.raise_for_status()
        for w in resp.json().get("results", []):
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            oa = w.get("open_access") or {}
            authors = [a["author"]["display_name"] for a in (w.get("authorships") or [])]
            venue_info = (w.get("primary_location") or {}).get("source") or {}
            papers.append({
                "id": f"openalex:{w.get('id', '').split('/')[-1]}",
                "title": w.get("display_name", ""),
                "abstract": w.get("abstract") or "",
                "authors": authors,
                "published": w.get("publication_date", ""),
                "source": "OpenAlex",
                "category": "index",
                "url": w.get("doi") or w.get("id", ""),
                "pdf_url": oa.get("oa_url"),
                "doi": doi or None,
                "citations": w.get("cited_by_count", 0),
                "venue": venue_info.get("display_name", "Unknown"),
                "open_access": oa.get("is_oa", False),
            })
    return papers


def fetch_crossref(config: dict) -> list[dict]:
    """Crossref API — no key, polite pool with mailto."""
    from_date = (datetime.now(timezone.utc) - timedelta(days=config["days_ago"])).strftime("%Y-%m-%d")
    params = {
        "query": config["query"],
        "rows": config["max_results"],
        "filter": f"from-pub-date:{from_date}",
        "sort": "published",
        "order": "desc",
        "mailto": "techpulse@example.com",
    }
    resp = requests.get("https://api.crossref.org/works", params=params, timeout=30)
    resp.raise_for_status()

    papers = []
    for item in resp.json().get("message", {}).get("items", []):
        doi = item.get("DOI", "")
        authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in (item.get("author") or [])]
        venue = (item.get("container-title") or ["Unknown"])[0]
        pub_date = item.get("published", {}).get("date-parts", [[""]])[0][0]
        papers.append({
            "id": f"crossref:{doi}",
            "title": (item.get("title") or [""])[0],
            "abstract": item.get("abstract") or "",
            "authors": authors,
            "published": str(pub_date),
            "source": "Crossref",
            "category": "index",
            "url": f"https://doi.org/{doi}",
            "pdf_url": None,
            "doi": doi,
            "citations": item.get("is-referenced-by-count", 0),
            "venue": venue,
            "open_access": False,
        })
    return papers


def fetch_dblp(config: dict) -> list[dict]:
    """dblp API — no key, covers all conferences & journals."""
    papers = []
    for stream in config["streams"]:
        # dblp search API
        params = {"format": "json", "h": config["max_results_per_stream"]}
        url = f"https://dblp.org/search/publ/api?q={stream.replace('/', '+')}&format=json&h={config['max_results_per_stream']}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        hits = resp.json().get("result", {}).get("hits", {}).get("hit", [])
        for h in hits:
            info = h.get("info", {})
            doi = info.get("doi")
            ee = info.get("ee", [])
            pdf_url = None
            if ee:
                # Look for PDF link in ee list
                for link in ee:
                    if link.endswith(".pdf"):
                        pdf_url = link
                        break
                if not pdf_url:
                    pdf_url = ee[0] if ee else None

            papers.append({
                "id": f"dblp:{info.get('key', '')}",
                "title": info.get("title", "").rstrip("."),
                "abstract": "",  # dblp doesn't provide abstracts
                "authors": [a["text"] for a in (info.get("authors", {}).get("author") or [])],
                "published": str(info.get("year", "")),
                "source": "dblp",
                "category": "conference" if info.get("type") == "Conference and Workshop Papers" else "journal",
                "url": pdf_url or f"https://dblp.org/rec/{info.get('key', '')}",
                "pdf_url": pdf_url,
                "doi": doi,
                "citations": 0,
                "venue": info.get("venue", "Unknown"),
                "open_access": pdf_url is not None,
            })
        time.sleep(0.5)
    return papers


def fetch_papers_with_code(config: dict) -> list[dict]:
    """Papers with Code API — no key."""
    papers = []
    for task in config["tasks"]:
        resp = requests.get(
            f"https://paperswithcode.com/api/v1/papers/?task={task}&limit={config['max_results_per_task']}",
            timeout=30
        )
        resp.raise_for_status()
        for p in resp.json().get("results", []):
            papers.append({
                "id": f"pwc:{p.get('id', '')}",
                "title": p.get("title", ""),
                "abstract": p.get("abstract") or "",
                "authors": p.get("authors", []),
                "published": (p.get("created_at") or "")[:10],
                "source": "Papers with Code",
                "category": "benchmark",
                "url": p.get("url", ""),
                "pdf_url": p.get("pdf_url"),
                "doi": None,
                "citations": p.get("citations", 0),
                "venue": p.get("venue") or "arXiv",
                "open_access": p.get("pdf_url") is not None,
            })
    return papers


def fetch_openreview(config: dict) -> list[dict]:
    """OpenReview API — no key for public data."""
    papers = []
    for venue in config["venues"]:
        # OpenReview v2 API
        params = {
            "content.venueid": venue,
            "limit": config["max_results_per_venue"],
            "sort": "cdate_desc",
        }
        resp = requests.get("https://api2.openreview.net/notes", params=params, timeout=30)
        if resp.status_code != 200:
            continue
        for note in resp.json().get("notes", []):
            content = note.get("content", {})
            title = content.get("title", {}).get("value", "") if isinstance(content.get("title"), dict) else content.get("title", "")
            abstract = content.get("abstract", {}).get("value", "") if isinstance(content.get("abstract"), dict) else content.get("abstract", "")
            authors = content.get("authors", {}).get("value", []) if isinstance(content.get("authors"), dict) else content.get("authors", [])
            pdf = content.get("pdf", {}).get("value", "") if isinstance(content.get("pdf"), dict) else content.get("pdf", "")
            pdf_url = f"https://openreview.net/pdf?id={note.get('id', '')}" if pdf else None

            papers.append({
                "id": f"openreview:{note.get('id', '')}",
                "title": title,
                "abstract": abstract,
                "authors": authors if isinstance(authors, list) else [authors],
                "published": str(note.get("cdate", "")),
                "source": "OpenReview",
                "category": "conference",
                "url": f"https://openreview.net/forum?id={note.get('id', '')}",
                "pdf_url": pdf_url,
                "doi": None,
                "citations": 0,
                "venue": venue,
                "open_access": pdf_url is not None,
            })
        time.sleep(0.5)
    return papers


def fetch_pubmed(config: dict) -> list[dict]:
    """PubMed E-utilities — no key, 3 req/sec."""
    terms = " OR ".join(config["search_terms"])
    search_params = {"db": "pubmed", "term": terms, "retmax": config["max_results"],
                     "sort": config["sort"], "retmode": "json"}
    resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                        params=search_params, timeout=30)
    resp.raise_for_status()
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    fetch_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                        params=fetch_params, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    papers = []
    for article in root.iter("PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle") or ""
        abs_parts = [t.text for t in article.findall(".//AbstractText") if t.text]
        abstract = " ".join(abs_parts)
        authors = [f"{a.findtext('ForeName','')} {a.findtext('LastName','')}".strip()
                   for a in article.findall(".//Author")]
        journal = article.findtext(".//Journal/Title") or "Unknown"
        year = article.findtext(".//PubDate/Year") or ""
        month = article.findtext(".//PubDate/Month") or ""
        day = article.findtext(".//PubDate/Day") or ""
        date_str = f"{year}-{month}-{day}".strip("-") if year else ""
        doi = article.findtext(".//ArticleId[@IdType='doi']")

        papers.append({
            "id": f"pubmed:{pmid}",
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": date_str,
            "source": "PubMed",
            "category": "journal",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "pdf_url": None,
            "doi": doi,
            "citations": 0,
            "venue": journal,
            "open_access": False,
        })
    return papers


def fetch_zenodo(config: dict) -> list[dict]:
    """Zenodo REST API — no key."""
    resp = requests.get(
        "https://zenodo.org/api/records",
        params={"q": "artificial intelligence OR machine learning",
                "sort": "mostrecent", "size": config["max_results"]},
        timeout=30
    )
    resp.raise_for_status()

    papers = []
    for rec in resp.json().get("hits", {}).get("hits", []):
        metadata = rec.get("metadata", {})
        title = metadata.get("title", "")
        desc = metadata.get("description", "")
        creators = [c.get("name", "") for c in metadata.get("creators", [])]
        doi = metadata.get("doi")
        # Find PDF among files
        pdf_url = None
        for f in rec.get("files", []):
            if f.get("key", "").endswith(".pdf"):
                pdf_url = f.get("links", {}).get("self")
                break

        papers.append({
            "id": f"zenodo:{rec.get('id', '')}",
            "title": title,
            "abstract": desc[:2000] if desc else "",
            "authors": creators,
            "published": rec.get("created", "")[:10],
            "source": "Zenodo",
            "category": "preprint",
            "url": rec.get("links", {}).get("html", ""),
            "pdf_url": pdf_url,
            "doi": doi,
            "citations": 0,
            "venue": "Zenodo",
            "open_access": pdf_url is not None,
        })
    return papers