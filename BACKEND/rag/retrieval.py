"""
retrieval.py
The only file needed for querying the knowledge base.

Call retrieve(query) with a plain text question — it automatically:
  1. Embeds the query using the same BGE model used at ingestion time
  2. Searches Qdrant-local using cosine similarity
  3. Formats the top-k matching chunks into a single text block,
     ready to be handed to the orchestrator/chat model as context

This file assumes embedding.py and qdrant_store.py sit alongside it in
this same RAG folder.
"""

from .embedding import embed_query
from .qdrant_store import client, COLLECTION_NAME, ensure_collection

TOP_K = 4  # number of chunks to retrieve per query


def retrieve(query: str, top_k: int = TOP_K) -> str:
    """
    Embeds the query and performs a cosine similarity search against the
    stored chunks in Qdrant. Returns a single formatted string containing
    the top matching chunks with their source citations, ready to be
    passed into the chat model's context.

    If no relevant chunks are found (or the collection is empty), returns
    an explicit "not found" message rather than an empty string, so the
    orchestrator can honestly tell the user nothing was retrieved.
    """
    ensure_collection()

    query_vector = embed_query(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    if not results:
        return "No relevant information was found in the knowledge base for this query."

    formatted_chunks = []
    for i, hit in enumerate(results, start=1):
        source = hit.payload.get("source", "unknown source")
        text = hit.payload.get("text", "")
        score = round(hit.score, 3)
        formatted_chunks.append(
            f"[Result {i} | Source: {source} | Relevance: {score}]\n{text}"
        )

    return "\n\n---\n\n".join(formatted_chunks)


if __name__ == "__main__":
    # quick manual test — run this file directly to sanity-check retrieval
    test_query = input("Enter a test query: ")
    print("\n" + retrieve(test_query))