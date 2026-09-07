"""
embedding.py
Handles converting text chunks into dense vectors using BAAI/bge-small-en-v1.5.

BGE models require mean pooling over token embeddings (with attention mask
applied) followed by L2 normalization — using the raw [CLS] token or skipping
normalization gives noticeably worse retrieval quality with BGE specifically.
"""

import torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "BAAI/bge-small-en-v1.5"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME, device_map="auto")
model.eval()  # inference only, no gradient tracking needed


def _mean_pooling(model_output, attention_mask):
    """
    Averages token embeddings, ignoring padded positions.
    """
    token_embeddings = model_output[0]  # (batch, seq_len, hidden_dim)
    input_mask_expanded = (
        attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    )
    summed = torch.sum(token_embeddings * input_mask_expanded, dim=1)
    counts = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
    return summed / counts


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Takes a list of text chunks, returns a list of normalized embedding vectors.
    Batches everything in a single forward pass for efficiency.
    """
    if not texts:
        return []

    # BGE recommends no special prefix for passages (only queries get "query: " prefix,
    # which is handled separately at retrieval time, not here)
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    encoded = {k: v.to(model.device) for k, v in encoded.items()}

    with torch.no_grad():
        model_output = model(**encoded)

    embeddings = _mean_pooling(model_output, encoded["attention_mask"])
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    return embeddings.cpu().tolist()


def embed_query(query: str) -> list[float]:
    """
    Embeds a single query string. BGE models perform better on retrieval
    tasks when queries are prefixed with 'query: ' — kept here even though
    retrieval isn't being built yet, so it's ready when you add it.
    """
    prefixed = f"query: {query}"
    return embed_texts([prefixed])[0]