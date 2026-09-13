"""Shared local LLM loading for tools that need on-device text generation
(summarize, translate). Runs via llama.cpp (llama-cpp-python) against a
GGUF model file - no network calls, no cloud fallback, matching PLAN.md's
"bundled or user-installed local models only" requirement.

The model itself is not bundled in this repo (a ~1GB binary, gitignored
under models/ per PLAN.md §10 - download it separately, see README). Every
call loads it fresh from disk: jobs run as one-shot subprocesses with no
state persisting between them (see engine/app/main.py), so there's no
process to keep a model warm in. That makes each summarize/translate job a
few seconds slower to start than every other tool - a known trade-off of
that architecture, not something to fix here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from engine.tools.common import ToolError

MODEL_FILENAME = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_CONTEXT_TOKENS = 4096


def _repo_root() -> Path:
    # engine/src/engine/tools/llm.py -> tools -> engine(pkg) -> src -> engine(project) -> repo root
    return Path(__file__).resolve().parents[4]


def model_path() -> Path:
    return _repo_root() / "models" / MODEL_FILENAME


def require_model() -> Path:
    path = model_path()
    if not path.is_file():
        raise ToolError(
            "LOCAL_MODEL_NOT_FOUND",
            f"Local AI model not found at {path}. Download {MODEL_FILENAME} into the project's "
            "models/ folder to use this tool (see README.md).",
        )
    return path


def load_llm() -> Any:
    try:
        from llama_cpp import Llama
    except ImportError as exc:  # noqa: BLE001
        raise ToolError(
            "LLM_RUNTIME_NOT_INSTALLED", "llama-cpp-python is not installed."
        ) from exc

    path = require_model()
    try:
        return Llama(model_path=str(path), n_ctx=MODEL_CONTEXT_TOKENS, verbose=False)
    except Exception as exc:  # noqa: BLE001
        raise ToolError("LOCAL_MODEL_LOAD_FAILED", f"Could not load the local model: {exc}") from exc


def generate(llm: Any, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
    except Exception as exc:  # noqa: BLE001
        raise ToolError("LLM_GENERATION_FAILED", f"Local model generation failed: {exc}") from exc

    return response["choices"][0]["message"]["content"].strip()
