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

import re
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
    "11. Pure Python numeric literals only: NEVER append physical unit letters directly to numbers "
    "(e.g. write 'D = 0.2  # meters' instead of 'D = 0.2m', and 'P = 350e6  # Pa' instead of 'P = 350e6 Pa').\n"
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_python_code(code_str: str) -> str:
    """Fix common LLM code generation quirks like unit suffixes on numbers."""
    cleaned_lines = []
    unit_pattern = re.compile(r'(\b\d+\.?\d*(?:e[+-]?\d+)?)\s*([a-zA-Z]+)(?=\s*([,\)\+\-\*\/]|\s*$))')

    for line in code_str.split("\n"):
        def _replace_unit(match):
            num = match.group(1)
            unit = match.group(2)
            if unit.lower() in ("e", "j"):  # scientific notation or imaginary number
                return match.group(0)
            if unit.lower() in ("m", "mm", "cm", "in", "k", "c", "pa", "mpa", "gpa", "bar", "psi", "s", "min", "hr", "kg", "g", "w", "v"):
                return f"{num}  # {unit}"
            return match.group(0)

        if "#" in line:
            code_part, comment_part = line.split("#", 1)
            fixed_code = unit_pattern.sub(_replace_unit, code_part)
            cleaned_lines.append(f"{fixed_code}#{comment_part}")
        else:
            fixed_code = unit_pattern.sub(_replace_unit, line)
            cleaned_lines.append(fixed_code)

    return "\n".join(cleaned_lines)


def build_code_prompt(user_request: str, context: Optional[str] = None) -> str:
    """Build the full prompt to send to the local Qwen model.

    Combines the system prompt with the user's engineering request and
    optional context (e.g., prior conversation, uploaded file contents).

    Parameters
    ----------
    user_request : str
        The engineering problem described by the user.
    context : Optional[str]
        Additional context (file contents, previous calculations, etc.).

    Returns
    -------
    str
        Complete prompt ready for ollama_client.
    """
    parts = [SYSTEM_PROMPT]

    if context:
        parts.append(f"CONTEXT / REFERENCE DATA:\n{context}\n")

    parts.append(
        f"ENGINEERING REQUEST:\n{user_request}\n\n"
        "Generate the Python code to solve this problem:"
    )

    return "\n".join(parts)


def extract_code_block(raw_response: str) -> str:
    """Extract and sanitize Python code from the model's markdown-fenced response."""
    extracted = ""
    if "```python" in raw_response:
        extracted = raw_response.split("```python")[1].split("```")[0].strip()
    elif "```" in raw_response:
        extracted = raw_response.split("```")[1].split("```")[0].strip()
    else:
        lines = raw_response.strip().split("\n")
        code_lines = []
        has_code_syntax = False
        
        for line in lines:
            stripped = line.strip()
            if (
                stripped.startswith(("import ", "from ", "def ", "class ", "print(", "return ", "if ", "for ", "while ", "#"))
                or "=" in stripped
                or stripped.endswith(":")
            ):
                code_lines.append(line)
                if not stripped.startswith("#"):
                    has_code_syntax = True
            elif not has_code_syntax:
                continue

        if code_lines and has_code_syntax:
            extracted = "\n".join(code_lines).strip()
        else:
            safe_text = raw_response.replace('"', '\\"').replace('\n', ' ')
            extracted = f'# Generated output (conversational)\nprint("{safe_text[:300]}...")'

    return sanitize_python_code(extracted)
