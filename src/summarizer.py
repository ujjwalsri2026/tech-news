from huggingface_hub import InferenceClient

_client = None
MODEL = "facebook/bart-large-cnn"


def _get_client():
    global _client
    if _client is None:
        _client = InferenceClient()
    return _client


def summarize(text: str, source_type: str = "news") -> str:
    client = _get_client()
    result = client.summarization(
        text,
        model=MODEL,
        truncation="longest_first",
        clean_up_tokenization_spaces=True,
    )
    return result.generated_text
