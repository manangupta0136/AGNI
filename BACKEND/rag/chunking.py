"""
chunking.py
Splits parsed document text into overlapping chunks suitable for embedding.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Tuned for SOP/manual-style documents: paragraph-sized chunks with enough
# overlap that a fact split across a chunk boundary is still recoverable.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_text(text: str, source_filename: str) -> list[dict]:
    """
    Splits raw text into chunks. Returns a list of dicts, each containing
    the chunk text plus metadata needed later for citation/traceability.
    """
    raw_chunks = splitter.split_text(text)

    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunks.append({
            "text": chunk,
            "source": source_filename,
            "chunk_index": i,
        })

    return chunks