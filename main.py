from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

from src.loader import load_urls
from src.scraper import fetch_raw, extract_articles, fetch_meta_description, fetch
from src.summarizer import summarize_short, preload
from src.saver import save


def process_source(source: dict) -> list[dict]:
    name = source["name"]
    url = source["url"]
    source_type = source.get("type", "news")
    use_jina = source.get("use_jina", False)
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    articles_out = []

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
        })

    return articles_out


def main():
    urls = load_urls()
    preload()
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(process_source, s): s for s in urls}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception:
                pass
    save(results)
    sources_with_articles = len({r["source"] for r in results})
    print(f"Done. {len(results)} articles from {sources_with_articles} sources saved.")


if __name__ == "__main__":
    main()
