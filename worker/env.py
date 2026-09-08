"""Spec §10 environment. `.env` then process env, then data/config.json."""
from __future__ import annotations

import os
from pathlib import Path

KEY_ENV = {
    "xai": ("XAI_API_KEY",),
    "gemini": ("GEMINI_API_KEY",),
    "elevenlabs": ("ELEVENLABS_API_KEY",),
    "pexels": ("PEXELS_API_KEY",),
    "pixabay": ("PIXABAY_API_KEY",),
    "unsplash": ("UNSPLASH_ACCESS_KEY",),
    "youtube": ("YOUTUBE_DATA_API_KEY", "YOUTUBE_API_KEY"),
    "serpapi": ("SERPAPI_KEY", "SERPAPI_API_KEY"),
}

SPEC_ENV = (
    "LLM_PROVIDER",
    "XAI_API_KEY",
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "PEXELS_API_KEY",
    "PIXABAY_API_KEY",
    "UNSPLASH_ACCESS_KEY",
    "YOUTUBE_DATA_API_KEY",
    "SERPAPI_KEY",
    "TTS_DEFAULT",
    "RENDER_ENGINE",
    "DATA_DIR",
    "MAX_CLIP_MS",
    "CONCURRENT_DOWNLOADS",
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
)

STOCK_KEYS = ("pexels", "pixabay", "unsplash")
DEFAULT_TTS = "edge"
DEFAULT_RENDER_ENGINE = "ffmpeg"
DEFAULT_MAX_CLIP_MS = 5000
DEFAULT_CONCURRENT_DOWNLOADS = 6
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.2"
LLM_NAMES = ("gemini", "grok", "ollama")


def load_dotenv(path: Path | None = None) -> None:
    dest = path or Path.cwd() / ".env"
    if not dest.is_file():
        return
    try:
        text = dest.read_text(encoding="utf-8")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if name and name not in os.environ:
            os.environ[name] = value


load_dotenv()


def env_first(*names: str) -> str:
    for name in names:
        value = (os.environ.get(name) or "").strip()
        if value:
            return value
    return ""


def env_key(name: str) -> str:
    for var in KEY_ENV.get(name, ()):
        value = (os.environ.get(var) or "").strip()
        if value:
            return value
    return ""


def parse_tts(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in {"eleven", "elevenlabs"}:
        return "elevenlabs"
    if value in {"kokoro", "openai", "studio"}:
        return value
    return DEFAULT_TTS


def parse_render_engine(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in {"remotion", "rendermedia", "renderMedia"}:
        return "remotion"
    return DEFAULT_RENDER_ENGINE


def parse_max_clip_ms(raw: str | None, fallback: int = DEFAULT_MAX_CLIP_MS) -> int:
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    if n <= 0:
        return fallback
    return max(400, min(DEFAULT_MAX_CLIP_MS, n))


def parse_concurrent(raw: str | None, fallback: int = DEFAULT_CONCURRENT_DOWNLOADS) -> int:
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    if n <= 0:
        return fallback
    return max(1, min(12, n))


def parse_llm_provider(raw: str | None) -> str:
    value = (raw or "").strip().lower()
    if value in {"gemini", "google"}:
        return "gemini"
    if value in {"grok", "xai"}:
        return "grok"
    if value in {"ollama", "local"}:
        return "ollama"
    return "auto"


def llm_provider() -> str:
    return parse_llm_provider(env_first("LLM_PROVIDER"))


def resolved_llm() -> str:
    """Concrete provider for this process. Explicit LLM_PROVIDER never falls through to another paid API."""
    choice = llm_provider()
    if choice == "gemini":
        return "gemini" if env_key("gemini") else "none"
    if choice == "grok":
        return "grok" if env_key("xai") else "none"
    if choice == "ollama":
        return "ollama"
    if env_key("gemini"):
        return "gemini"
    if env_key("xai"):
        return "grok"
    return "none"


def llm_is(name: str) -> bool:
    return resolved_llm() == name


def ollama_host() -> str:
    return env_first("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST


def ollama_model() -> str:
    return env_first("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL


def data_root() -> Path:
    raw = env_first("DATA_DIR", "LUMENCUT_DATA_DIR")
    if raw:
        path = Path(raw)
        return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
    return (Path.cwd() / "data").resolve()


def max_clip_ms(file_value: int | None = None) -> int:
    raw = env_first("MAX_CLIP_MS")
    if raw:
        return parse_max_clip_ms(raw)
    if file_value:
        return parse_max_clip_ms(str(file_value))
    return DEFAULT_MAX_CLIP_MS


def concurrent_downloads(file_value: int | None = None) -> int:
    raw = env_first("CONCURRENT_DOWNLOADS")
    if raw:
        return parse_concurrent(raw)
    if file_value:
        return parse_concurrent(str(file_value))
    return DEFAULT_CONCURRENT_DOWNLOADS


def tts_from(file_value: str = "") -> str:
    return parse_tts(env_first("TTS_DEFAULT") or file_value or DEFAULT_TTS)


def render_engine_from(file_value: str = "") -> str:
    return parse_render_engine(env_first("RENDER_ENGINE") or file_value or DEFAULT_RENDER_ENGINE)


def has_stock_key() -> bool:
    return any(env_key(name) for name in STOCK_KEYS)
