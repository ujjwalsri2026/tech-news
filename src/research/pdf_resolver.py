"""
PDF resolver: Unpaywall -> arXiv search -> Semantic Scholar fallback.
"""
import time
import requests


def resolve_pdf(paper, email="techpulse@example.com"):
    if paper.get("pdf_url"):
        return paper

    doi = paper.get("doi")

    # Step 1: Unpaywall
    if doi:
        try:
            resp = requests.get(
                f"https://api.unpaywall.org/v2/{doi}",
                params={"email": email}, timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                best = data.get("best_oa_location") or {}
                pdf = best.get("url_for_pdf") or best.get("url")
                if pdf:
                    paper["pdf_url"] = pdf
                    paper["open_access"] = True
                    return paper
        except Exception:
            pass

    # Step 2: arXiv search by title
    try:
        title = paper.get("title", "")
        if title:
            resp = requests.get(
                "http://export.arxiv.org/api/query",
                params={"search_query": f"ti:{title}", "max_results": 3}, timeout=15
            )
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns):
                    arxiv_title = " ".join(entry.find("atom:title", ns).text.split())
                    if title.lower()[:50] in arxiv_title.lower() or arxiv_title.lower()[:50] in title.lower():
                        arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
                        paper["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}"
                        paper["open_access"] = True
                        return paper
    except Exception:
        pass

    # Step 3: Semantic Scholar
    try:
        title = paper.get("title", "")
        if title:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": title, "limit": 3, "fields": "title,openAccessPdf"},
                timeout=15
            )
            if resp.status_code == 200:
                for p in resp.json().get("data", []):
                    if p.get("title", "").lower()[:50] in title.lower() or title.lower()[:50] in p.get("title", "").lower():
                        oa = p.get("openAccessPdf")
                        if oa and oa.get("url"):
                            paper["pdf_url"] = oa["url"]
                            paper["open_access"] = True
                            return paper
                time.sleep(1.1)
    except Exception:
        pass

    return paper


def batch_resolve_pdfs(papers):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(resolve_pdf, p): p for p in papers}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                results.append(futures[future])
    return results