"""
AI summarizer using local Hugging Face models.
Uses DistilBART (240MB) as primary, BART-large-CNN as fallback.
Lazy-loaded -- models only downloaded on first use.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_distilbart_model = None
_distilbart_tokenizer = None
_bart_model = None
_bart_tokenizer = None


def _load_distilbart():
    global _distilbart_model, _distilbart_tokenizer
    if _distilbart_model is None:
        print("[summarizer] Loading DistilBART...")
        _distilbart_tokenizer = AutoTokenizer.from_pretrained("sshleifer/distilbart-cnn-6-6")
        _distilbart_model = AutoModelForSeq2SeqLM.from_pretrained("sshleifer/distilbart-cnn-6-6")
        _distilbart_model.eval()
        print("[summarizer] DistilBART loaded.")
    return _distilbart_tokenizer, _distilbart_model


def _load_bart():
    global _bart_model, _bart_tokenizer
    if _bart_model is None:
        print("[summarizer] Loading BART-large-CNN...")
        _bart_tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
        _bart_model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
        _bart_model.eval()
        print("[summarizer] BART loaded.")
    return _bart_tokenizer, _bart_model


def summarize(text, max_length=80, min_length=25):
    if not text or len(text) < 100:
        return text

    try:
        tokenizer, model = _load_distilbart()
        inputs = tokenizer(text[:1024], return_tensors="pt", max_length=1024, truncation=True)
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"], max_length=max_length, min_length=min_length,
                num_beams=2, early_stopping=True,
            )
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
    except Exception as e:
        print(f"[summarizer] DistilBART failed: {e}")

    try:
        tokenizer, model = _load_bart()
        inputs = tokenizer(text[:1024], return_tensors="pt", max_length=1024, truncation=True)
        with torch.no_grad():
            summary_ids = model.generate(
                inputs["input_ids"], max_length=max_length, min_length=min_length,
                num_beams=2, early_stopping=True,
            )
        return tokenizer.decode(summary_ids[0], skip_special_tokens=True).strip()
    except Exception as e:
        print(f"[summarizer] BART failed: {e}")
        return text


def batch_summarize(papers, max_length=80, min_length=25):
    print("[summarizer] Pre-loading models for batch processing...")
    try:
        _load_distilbart()
    except Exception:
        pass
    try:
        _load_bart()
    except Exception:
        pass

    for paper in papers:
        abstract = paper.get("abstract", "")
        if abstract and len(abstract) > 100:
            try:
                paper["ai_summary"] = summarize(abstract, max_length, min_length)
            except Exception:
                paper["ai_summary"] = abstract[:200]
        else:
            paper["ai_summary"] = abstract[:200] if abstract else "No abstract available."
    return papers