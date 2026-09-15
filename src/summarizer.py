from transformers import pipeline

_pipe = None
MODEL = "facebook/bart-large-cnn"


def _get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = pipeline("summarization", model=MODEL)
    return _pipe


def summarize(text: str, source_type: str = "news") -> str:
    p = _get_pipe()
    result = p(
        text,
        max_length=150,
        min_length=30,
        do_sample=False,
        truncation=True,
    )
    return result[0]["summary_text"]
