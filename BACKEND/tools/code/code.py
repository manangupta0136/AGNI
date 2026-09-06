"""
code.py — Local Python Code Execution Engine for AGNI.

Executes AI-generated Python scripts inside `BACKEND/workspace/` via
subprocess isolation. Designed as the tool backend invoked by `brain.py`
in the main agent loop.

Contract
--------
    execute_code(code_string: str) -> dict
        Success  → {"status": "success", "output": "<stdout>"}
        Error    → {"status": "error",   "output": "<stderr | traceback>"}
        Timeout  → {"status": "error",   "output": "Execution timed out after 15 seconds."}

Security notes
--------------
- All script execution uses ``subprocess.run`` with ``cwd=WORKSPACE_DIR``,
  so every relative path in the generated script resolves inside the
  shared workspace — not the project root or system directories.
- A hard 15-second timeout prevents infinite loops and runaway processes.
- Temporary script files are unconditionally deleted in a ``finally`` block.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict

from code_tools.code_prompt import (
    SYSTEM_PROMPT,
    build_code_prompt,
    extract_code_block,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXECUTION_TIMEOUT_SECONDS: int = 15
"""Hard upper bound (in seconds) for any single script execution."""

WORKSPACE_DIR: Path = (Path(__file__).resolve().parent.parent / "workspace")
"""
Absolute path to ``BACKEND/workspace/``.

Resolved dynamically relative to *this* file so the project can be cloned
anywhere without breaking path assumptions.  Created on import if absent.
"""

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Primary public API
# ---------------------------------------------------------------------------

def execute_code(code_string: str) -> Dict[str, str]:
    """Execute a Python code string in an isolated subprocess.

    The script is written to a secure temporary file inside the workspace
    directory, executed with the current Python interpreter, and then
    unconditionally cleaned up.

    Parameters
    ----------
    code_string : str
        Raw Python source code to execute.

    Returns
    -------
    dict
        ``{"status": "success" | "error", "output": str}``

        * **success** — captured ``stdout`` (stripped).
        * **error**   — captured ``stderr`` (or ``stdout`` when ``stderr``
          is empty), or a descriptive timeout / exception message.
    """
    temp_script_path: str | None = None

    try:
        # ── 1. Write code to a secure temp file inside the workspace ──
        fd, temp_script_path = tempfile.mkstemp(
            suffix=".py",
            prefix="agni_exec_",
            dir=str(WORKSPACE_DIR),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as script_file:
            script_file.write(code_string)

        # ── 2. Run the script in a subprocess ─────────────────────────
        result: subprocess.CompletedProcess[str] = subprocess.run(
            [sys.executable, temp_script_path],
            capture_output=True,
            text=True,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            cwd=str(WORKSPACE_DIR),
        )

        # ── 3. Interpret the result ───────────────────────────────────
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout.strip(),
            }

        # Non-zero exit — prefer stderr; fall back to stdout.
        error_output: str = (
            result.stderr.strip() if result.stderr.strip() else result.stdout.strip()
        )
        return {
            "status": "error",
            "output": error_output,
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "output": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS} seconds.",
        }

    except Exception as exc:
        return {
            "status": "error",
            "output": f"Execution failed: {exc}",
        }

    finally:
        # ── 4. Unconditional cleanup ──────────────────────────────────
        if temp_script_path is not None and os.path.exists(temp_script_path):
            try:
                os.remove(temp_script_path)
            except OSError:
                pass  # Best-effort removal; don't mask the real error.


# ---------------------------------------------------------------------------
# Self-test harness
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    DIVIDER = "=" * 60

    # ── Test 1: Successful execution & stdout capture ─────────────
    print(DIVIDER)
    print("TEST 1 — Successful execution (print + math)")
    print(DIVIDER)
    result_1 = execute_code(
        "import math\n"
        "print(f'pi = {math.pi:.6f}')\n"
        "print(f'sqrt(2) = {math.sqrt(2):.6f}')\n"
    )
    print(json.dumps(result_1, indent=2))
    assert result_1["status"] == "success", f"Expected success, got {result_1}"

    # ── Test 2: Error capture (ZeroDivisionError) ─────────────────
    print(f"\n{DIVIDER}")
    print("TEST 2 — Runtime error capture (ZeroDivisionError)")
    print(DIVIDER)
    result_2 = execute_code("x = 1 / 0\n")
    print(json.dumps(result_2, indent=2))
    assert result_2["status"] == "error", f"Expected error, got {result_2}"
    assert "ZeroDivisionError" in result_2["output"], (
        f"Expected ZeroDivisionError in output, got: {result_2['output']}"
    )

    # ── Test 3: Timeout prevention ────────────────────────────────
    print(f"\n{DIVIDER}")
    print("TEST 3 — Timeout prevention (sleep 20s > 15s limit)")
    print(DIVIDER)
    result_3 = execute_code("import time\ntime.sleep(20)\n")
    print(json.dumps(result_3, indent=2))
    assert result_3["status"] == "error", f"Expected error, got {result_3}"
    assert "timed out" in result_3["output"].lower(), (
        f"Expected timeout message, got: {result_3['output']}"
    )

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("ALL 3 TESTS PASSED [OK]")
    print(DIVIDER)
