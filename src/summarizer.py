import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

_tokenizer = None
_model = None
MODEL = "facebook/bart-large-cnn"


def _load():
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL)


def summarize(text: str, source_type: str = "news") -> str:
    _load()
    inputs = _tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)
    with torch.no_grad():
        output = _model.generate(
            **inputs,
            max_length=150,
            min_length=30,
            do_sample=False,
        )
    return _tokenizer.decode(output[0], skip_special_tokens=True)
