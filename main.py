from concurrent.futures import ThreadPoolExecutor, as_completed

from src.loader import load_urls
from src.scraper import fetch
from src.summarizer import summarize
from src.saver import save


def process_source(source: dict) -> dict:
    name = source["name"]
    url = source["url"]
    source_type = source.get("type", "news")
    use_jina = source.get("use_jina", False)
    try:
        text = fetch(url, use_jina=use_jina)
        summary = summarize(text, source_type)
        return {"source": name, "url": url, "type": source_type, "summary": summary}
    except Exception as e:
        return {"source": name, "url": url, "type": source_type, "summary": f"\u26a0\ufe0f Failed: {e}"}


def main():
    urls = load_urls()
    results = []
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(process_source, s): s for s in urls}
        for future in as_completed(futures):
            results.append(future.result())
    save(results)
    success = sum(1 for r in results if not r["summary"].startswith("\u26a0\ufe0f"))
    print(f"Done. {success}/{len(results)} entries saved.")


if __name__ == "__main__":
    main()
