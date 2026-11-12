"""
Shared GroqCloud LLM Client & Generation Helpers.
Centralizes Groq client instantiation, chat completion calls, and JSON parsing.
"""

import json
import os
from typing import Any, Dict, List, Optional

from groq import Groq

from app.core.config import settings


def get_groq_client() -> Groq:
    """Create a Groq client using configured settings or environment variables."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    return Groq(api_key=api_key)


def _strip_markdown_fences(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


FALLBACK_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


def generate_text(
    prompt: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    json_mode: bool = False,
    model: Optional[str] = None,
    client: Optional[Groq] = None,
) -> str:
    """Execute a Groq chat completion and return the assistant text content."""
    active_client = client or get_groq_client()
    requested_model = model or settings.GROQ_MODEL
    models_to_try = [requested_model] + [m for m in FALLBACK_MODELS if m != requested_model]

    last_error = None
    for target_model in models_to_try:
        kwargs: Dict[str, Any] = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = active_client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            err_str = str(e).lower()
            if "model_not_found" in err_str or "does not exist" in err_str or "404" in err_str:
                last_error = e
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("No models available for generation.")


def generate_json(
    prompt: str,
    *,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    model: Optional[str] = None,
    client: Optional[Groq] = None,
) -> Any:
    """Execute a Groq chat completion in JSON mode and return the parsed payload."""
    raw = generate_text(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=True,
        model=model,
        client=client,
    )
    return json.loads(_strip_markdown_fences(raw))


def generate_json_list(
    prompt: str,
    list_key: str,
    *,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    model: Optional[str] = None,
    client: Optional[Groq] = None,
) -> List[Dict[str, Any]]:
    """
    Execute a Groq JSON completion and unwrap a list of objects.
    Groq json_object mode returns a top-level JSON object, so wrapped arrays are extracted safely.
    """
    data = generate_json(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model,
        client=client,
    )
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get(list_key), list):
            return data[list_key]
        for val in data.values():
            if isinstance(val, list):
                return val
    return []
