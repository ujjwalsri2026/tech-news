"""
PDF resolver: Unpaywall -> Europe PMC -> arXiv -> Semantic Scholar.

Europe PMC is keyless and authoritative for biomed, and its open-access subset
is large, so it is worth a lookup before the two slower title-search fallbacks.
"""
import time
import requests

EUROPE_PMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def _resolve_europe_pmc(paper) -> bool:
    """Look up PubMed Central via Europe PMC. Sets pdf_url on success."""
    doi = paper.get("doi")
    if not doi:
        return False
    try:
        resp = requests.get(
            EUROPE_PMC,
            params={"query": f'DOI:"{doi}"', "format": "json", "pageSize": 1},
            timeout=15
        )
        if resp.status_code != 200:
            return False
        results = resp.json().get("resultList", {}).get("result", [])
        if not results:
            return False
        rec = results[0]
        if str(rec.get("isOpenAccess", "N")).upper() != "Y":
            return False
        pmcid = rec.get("pmcid")
        if not pmcid:
            return False
        paper["pdf_url"] = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
        paper["open_access"] = True
        if not paper.get("abstract"):
            paper["abstract"] = rec.get("abstractText", "") or ""
        return True
    except Exception:
        return False


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

    # Step 2: Europe PMC / PubMed Central
    if doi and _resolve_europe_pmc(paper):
        return paper

    # Step 3: arXiv search by title
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

    # Step 4: Semantic Scholar
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