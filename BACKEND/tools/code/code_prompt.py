"""
code_prompt.py — System prompt templates for AGNI code generation.

Provides structured prompt templates that instruct the local Qwen model
to produce clean, executable Python code for MRPL engineering tasks.

Usage
-----
    from code_tools.code_prompt import build_code_prompt

    prompt = build_code_prompt("Calculate pressure drop in a 100m pipe...")
"""

from __future__ import annotations

from typing import Optional

# ---------------------------------------------------------------------------
# Core system prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = (
    "You are AGNI, an expert AI engineering assistant deployed at "
    "Mangalore Refinery and Petrochemicals Limited (MRPL). "
    "You operate in a fully air-gapped, offline environment.\n\n"

    "ROLE:\n"
    "- You solve chemical, mechanical, and process engineering problems "
    "by writing Python code.\n"
    "- You specialize in: fluid mechanics, heat transfer, thermodynamics, "
    "reaction engineering, process control, and sensor data analysis.\n\n"

    "CODE RULES (STRICT):\n"
    "1. Output ONLY valid Python code inside a single ```python block.\n"
    "2. Do NOT include any markdown text, explanations, or commentary "
    "outside the code block.\n"
    "3. Use standard libraries: numpy, scipy, matplotlib, pandas, math.\n"
    "4. All file reads/writes (CSV, images, plots) MUST use relative paths "
    "only (e.g., 'output.csv', 'chart.png'). Never use absolute paths.\n"
    "5. Always print the final results to stdout with clear labels.\n"
    "6. For plots, always call plt.savefig('chart.png', dpi=150, "
    "bbox_inches='tight') AND plt.close() — never call plt.show().\n"
    "7. Add brief inline comments explaining each engineering formula used.\n"
    "8. Handle edge cases (division by zero, negative sqrt) gracefully.\n"
    "9. Use SI units unless the user specifies otherwise.\n"
    "10. Print intermediate calculation steps so the engineer can verify.\n"
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_code_prompt(user_request: str, context: Optional[str] = None) -> str:
    """Build the full prompt to send to the local Qwen model.

    Combines the system prompt with the user's engineering request and
    optional context (e.g., prior conversation, uploaded file contents).

    Parameters
    ----------
    user_request : str
        The engineer's natural-language task description.
    context : str, optional
        Additional context such as file contents, sensor data summaries,
        or prior conversation history to ground the model's response.

    Returns
    -------
    str
        A fully assembled prompt string ready for the Ollama API.
    """
    parts: list[str] = [SYSTEM_PROMPT]

    if context:
        parts.append(f"CONTEXT:\n{context}\n")

    parts.append(f"USER REQUEST:\n{user_request}")

    return "\n".join(parts)


def extract_code_block(raw_response: str) -> str:
    """Extract Python code from the model's markdown-fenced response.

    Handles three cases:
    1. Code inside ```python ... ``` fences (preferred).
    2. Code inside generic ``` ... ``` fences.
    3. Raw response with no fences (treated as code directly).

    Parameters
    ----------
    raw_response : str
        The raw text response from the Ollama model.

    Returns
    -------
    str
        Cleaned Python source code ready for execution.
    """
    if "```python" in raw_response:
        return raw_response.split("```python")[1].split("```")[0].strip()

    if "```" in raw_response:
        return raw_response.split("```")[1].split("```")[0].strip()

    return raw_response.strip()
