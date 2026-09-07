"""
tools/rag.py
LLM-tool wrapper around rag/retrieval.py's retrieve(). This is the
function-calling entrypoint brain.py binds to the orchestrator LLM.
"""

from langchain_core.tools import tool

from rag.retrieval import retrieve


@tool
def rag_search(query: str) -> str:
    """Search the organization's local knowledge base (SOPs, manuals, correspondence) for relevant information."""
    return retrieve(query)
