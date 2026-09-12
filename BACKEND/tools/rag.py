"""
tools/rag.py
LLM-tool wrapper around rag/retrieval.py's retrieve(). This is the
function-calling entrypoint brain.py binds to the orchestrator LLM.
"""

from langchain_core.tools import tool

try:
    from rag.retrieval import retrieve
except Exception as e:
    def retrieve(query: str, top_k: int = 4) -> str:
        return f"[Knowledge base retrieval offline: {e}]"


@tool
def rag_search(query: str) -> str:
    """Search the organization's local knowledge base (SOPs, manuals, correspondence) for relevant information."""
    return retrieve(query)
