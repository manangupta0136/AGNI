"""
pdf.py — PDF tool for AGNI.

Stub implementation: the real PDF generation/parsing logic is not yet
built. Exposed as a bound tool so the orchestrator can call it and get a
clear "in development" response instead of failing.
"""

from langchain_core.tools import tool


@tool
def pdf_tool(query: str) -> str:
    """Generate or read PDF documents. Currently under development."""
    return "[PDF tool is under development]"
