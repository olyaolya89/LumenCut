"""LLM router. Only the provider in LLM_PROVIDER is called; search/TTS/ffmpeg stay free."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from worker.env import env_key, llm_is, ollama_host, ollama_model, resolved_llm

TEMPERATURE = 0.3


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: float = 22.0) -> Any | None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return None


def grok_json(system: str, user: str, schema: dict, name: str) -> str | None:
    api_key = env_key("xai")
    if not api_key:
        return None
    body = {
        "model": "grok-4.5",
        "temperature": TEMPERATURE,
        "max_tokens": 3500,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}},
    }
    data = _post_json("https://api.x.ai/v1/chat/completions", body, {"Authorization": f"Bearer {api_key}"})
    if not data:
        body["response_format"] = {"type": "json_object"}
        data = _post_json("https://api.x.ai/v1/chat/completions", body, {"Authorization": f"Bearer {api_key}"})
    if not isinstance(data, dict):
        return None
    choices = data.get("choices") or []
    if not choices:
        return None
    return ((choices[0] or {}).get("message") or {}).get("content")


def gemini_json(system: str, user: str) -> str | None:
    api_key = env_key("gemini")
    if not api_key:
        return None
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": TEMPERATURE, "responseMimeType": "application/json", "maxOutputTokens": 3500},
    }
    for model in ("gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        data = _post_json(url, payload, {})
        if not isinstance(data, dict):
            continue
        parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
        text = "".join(str(p.get("text") or "") for p in parts)
        if text.strip():
            return text
    return None


def ollama_json(system: str, user: str) -> str | None:
    host = ollama_host().rstrip("/")
    payload = {
        "model": ollama_model(),
        "stream": False,
        "format": "json",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"temperature": TEMPERATURE},
    }
    data = _post_json(f"{host}/api/chat", payload, {}, timeout=60.0)
    if not isinstance(data, dict):
        return None
    message = data.get("message") or {}
    text = message.get("content") if isinstance(message, dict) else None
    return str(text).strip() if text else None


def chat_json(system: str, user: str, schema: dict, name: str) -> tuple[str | None, str]:
    provider = resolved_llm()
    if provider == "gemini":
        text = gemini_json(system, user)
        return (text, "gemini") if text else (None, "heuristic")
    if provider == "grok":
        text = grok_json(system, user, schema, name)
        return (text, "grok") if text else (None, "heuristic")
    if provider == "ollama":
        text = ollama_json(system, user)
        return (text, "ollama") if text else (None, "heuristic")
    return None, "heuristic"


def allows_imagine() -> bool:
    """Image generation is the paid extra — only Grok Imagine when LLM_PROVIDER=grok."""
    return llm_is("grok")
