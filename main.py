import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

from src.loader import load_urls
from src.scraper import (
    fetch_raw,
    extract_articles,
    fetch_meta_description,
    fetch,
    parse_rss,
)
from src.summarizer import summarize_short, preload
from src.saver import save


def load_rss_map() -> dict:
    p = Path("data/rss.json")
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def process_source(source: dict, rss_map: dict) -> list[dict]:
    name = source["name"]
    url = source["url"]
    source_type = source.get("type", "news")
    use_jina = source.get("use_jina", False)
    rss_url = rss_map.get(name, "")
    articles_out = []

    rss_items = parse_rss(rss_url) if rss_url else []

    if rss_items:
        for item in rss_items:
            desc = ""
            try:
                art_html = fetch_raw(item["url"], use_jina)
                desc = fetch_meta_description(art_html)
            except Exception:
                pass
            articles_out.append({
                "source": name,
                "type": source_type,
                "title": item["title"],
                "url": item["url"],
                "description": desc,
                "via": "rss",
            })
        return articles_out

    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    try:
        html = fetch_raw(url, use_jina)
        articles = extract_articles(html, base_url)
    except Exception as e:
        return [{
            "source": name,
            "type": source_type,
            "title": f"Failed to load {name}",
            "url": url,
            "description": str(e),
            "via": "scrape",
        }]

    if not articles:
        try:
            text = fetch(url, use_jina=use_jina)
            desc = summarize_short(text) if len(text) > 200 else text[:300]
        except Exception:
            desc = ""
        return [{
            "source": name,
            "type": source_type,
            "title": name,
            "url": url,
            "description": desc,
            "via": "scrape",
        }]

    for art in articles:
        desc = ""
        try:
            art_html = fetch_raw(art["url"], use_jina)
            desc = fetch_meta_description(art_html)
        except Exception:
            pass

        if not desc:
            try:
                art_text = fetch(art["url"], use_jina=use_jina)
                if len(art_text) > 200:
                    desc = summarize_short(art_text)
                else:
                    desc = art_text[:300]
            except Exception:
                desc = ""

        articles_out.append({
            "source": name,
            "type": source_type,
            "title": art["title"],
            "url": art["url"],
            "description": desc,
            "via": "scrape",
        })

    return articles_out


def main():
    urls = load_urls()
    rss_map = load_rss_map()
    rss_sources = sum(1 for s in urls if rss_map.get(s["name"]))
    print(f"RSS feeds available for {rss_sources}/{len(urls)} sources")
    preload()
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(process_source, s, rss_map): s
            for s in urls
        }
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception:
                pass
    save(results)
    rss_count = sum(1 for r in results if r.get("via") == "rss")
    scrape_count = len(results) - rss_count
    print(f"Done. {len(results)} articles ({rss_count} RSS, {scrape_count} scraped) saved.")

    # ─── RESEARCH PIPELINE ───
    print("\n[research] Starting research pipeline...")
    try:
        from src.research.aggregator import run_aggregator
        from src.research.saver import save_papers

        research_config = json.loads(Path("data/research_sources.json").read_text())
        papers = run_aggregator(research_config, do_summarize=True)
        save_papers(papers)
        print(f"[research] Done. {len(papers)} papers saved.")
    except Exception as e:
        print(f"[research] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
