"""
Research aggregator -- merge all sources, dedupe, enrich PDFs, batch summarize, sort.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from research.api_sources import (
    fetch_arxiv, fetch_semantic_scholar, fetch_openalex,
    fetch_crossref, fetch_dblp, fetch_papers_with_code,
    fetch_openreview, fetch_pubmed, fetch_zenodo
)
from research.scrape_sources import run_all_scrape_sources
from research.pdf_resolver import batch_resolve_pdfs
from research.summarizer import batch_summarize


def _dedupe(papers):
    seen_ids = set()
    seen_titles = set()
    deduped = []
    for p in papers:
        pid = p.get("id", "")
        title_norm = " ".join(p.get("title", "").lower().split())
        if pid in seen_ids or title_norm in seen_titles:
            continue
        seen_ids.add(pid)
        seen_titles.add(title_norm)
        deduped.append(p)
    return deduped


def run_aggregator(config, do_summarize=True):
    api_cfg = config.get("api_sources", {})
    scrape_cfg = config.get("scrape_sources", {})
    all_papers = []

    print("[research] Running API sources...")
    api_fetchers = {
        "arxiv": fetch_arxiv,
        "semantic_scholar": fetch_semantic_scholar,
        "openalex": fetch_openalex,
        "crossref": fetch_crossref,
        "dblp": fetch_dblp,
        "papers_with_code": fetch_papers_with_code,
        "openreview": fetch_openreview,
        "pubmed": fetch_pubmed,
        "zenodo": fetch_zenodo,
    }
    for name, fetcher in api_fetchers.items():
        src = api_cfg.get(name, {})
        if src.get("enabled", True):
            try:
                papers = fetcher(src)
                print(f"  [+] {name}: {len(papers)} papers")
                all_papers.extend(papers)
            except Exception as e:
                print(f"  [!] {name}: {e}")

    print("[research] Running scrape sources...")
    scrape_papers = run_all_scrape_sources(scrape_cfg)
    print(f"  [+] Scrape sources: {len(scrape_papers)} papers")
    all_papers.extend(scrape_papers)

    print(f"[research] Before dedup: {len(all_papers)}")
    all_papers = _dedupe(all_papers)
    print(f"[research] After dedup: {len(all_papers)}")

    print("[research] Resolving PDFs...")
    all_papers = batch_resolve_pdfs(all_papers)
    oa_count = sum(1 for p in all_papers if p.get("pdf_url"))
    print(f"  [+] PDFs found: {oa_count}/{len(all_papers)}")

    if do_summarize:
        print("[research] Generating AI summaries (this may take a while)...")
        all_papers = batch_summarize(all_papers)
        print("[research] Summaries complete.")

    all_papers.sort(key=lambda p: (
        p.get("published", "")[:10],
        p.get("citations", 0)
    ), reverse=True)

    return all_papers