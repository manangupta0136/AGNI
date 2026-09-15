"""
qdrant_store.py
Sets up a local, embedded Qdrant instance (file-persisted, no server, no
network calls) and provides a function to store embedded chunks into it.
"""

import uuid
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

QDRANT_PATH = str(Path(__file__).parent.parent / "data" / "qdrant_db")   # persisted locally on disk
COLLECTION_NAME = "mrpl_knowledge_base"
EMBEDDING_DIM = 384                 # bge-small-en-v1.5 output dimension

_client = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(path=QDRANT_PATH)
    return _client


class _LazyClientProxy:
    def __getattr__(self, name):
        return getattr(get_qdrant_client(), name)


client = _LazyClientProxy()


def ensure_collection():
    """
    Creates the collection if it doesn't already exist. Safe to call every
    time — it checks first rather than blindly recreating.
    """
    q_client = get_qdrant_client()
    existing = [c.name for c in q_client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        q_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"[qdrant_store] Created collection '{COLLECTION_NAME}'")
    else:
        print(f"[qdrant_store] Using existing collection '{COLLECTION_NAME}'")


def store_chunks(chunks: list[dict], embeddings: list[list[float]]):
    """
    Stores chunks + their embeddings into Qdrant. Each chunk dict is expected
    to have 'text', 'source', and 'chunk_index' keys (from chunking.py).
    """
    ensure_collection()

    points = []
    for chunk, vector in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"[qdrant_store] Stored {len(points)} chunks from '{chunks[0]['source']}'" if chunks else "[qdrant_store] No chunks to store")