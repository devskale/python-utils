"""
Utils Module

Shared utilities for LLM-based workflows in procurement auditing.

Includes functions for robust JSON parsing from LLM responses and creating Agno agents.

Dependencies:
- json, re for parsing
- credgoo for API key management
- agno for LLM agent integration
- Optional: json_repair for fixing malformed JSON

Usage:
    from utils import extract_json_clean, create_agent
"""

import json
import re
from credgoo import get_api_key
from agno.agent import Agent
from agno.models.vllm import VLLM

# Optional JSON repair for messy LLM outputs
try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    repair_json = None  # type: ignore

# ---------------- Environment / Model selection -----------------
PROVIDER = "tu"
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
MODEL = "glm-4.5-355b"

api_key = get_api_key(PROVIDER)


def create_agent():
    """Create and return an Agno Agent with VLLM model."""
    return Agent(
        model=VLLM(
            base_url=BASE_URL,
            api_key=api_key,
            id=MODEL,
            max_retries=3,
            # stream=True,
        ),
        tools=[],
    )


def extract_json_clean(text: str):
    """Try to extract/parse JSON from a possibly noisy LLM response.

    Strategy:
    - Try direct json.loads
    - Try fenced code blocks ```json ... ``` or ``` ... ```
    - Try extracting just the matches array
    - Try using json_repair.repair_json when available
    Returns a Python object (dict or list) or None.
    """
    if not text:
        return None
    # 1) Direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) Look for fenced json blocks
    for pattern in [r"```json\s*(.*?)```", r"```\s*(.*?)```"]:
        m = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if m:
            block = m.group(1).strip()
            try:
                return json.loads(block)
            except Exception:
                # Attempt repair on the block if available
                if repair_json:
                    try:
                        fixed = repair_json(block)
                        return json.loads(fixed)
                    except Exception:
                        pass
                continue

    # 3) Extract just the matches array and wrap it
    m2 = re.search(r'"matches"\s*:\s*(\[.*?\])', text, flags=re.DOTALL)
    if m2:
        arr_text = m2.group(1)
        try:
            matches = json.loads(arr_text)
            return {"matches": matches}
        except Exception:
            # Attempt repair on the array if available
            if repair_json:
                try:
                    fixed_arr = repair_json(arr_text)
                    matches = json.loads(fixed_arr)
                    return {"matches": matches}
                except Exception:
                    pass
            pass

    # 4) Last resort: try to repair the entire text
    if repair_json:
        try:
            fixed_all = repair_json(text)
            return json.loads(fixed_all)
        except Exception:
            pass

    return None
