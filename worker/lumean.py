"""Lumean Public API — catalogue voices and TTS.

BASE https://api.lumean.app/api/public
Auth header X-API-KEY.

TTS is template-then-order. There is no orders.voice_id.
Voice lives in template.config.tts_settings.voice_id.
page for /voices/elevenlabs/library starts at 0.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

LUMEAN_BASE = "https://api.lumean.app/api/public"
LUMEAN_MAX_CHARS = 2500
POLL_SEC = 1.6
POLL_TRIES = 45
LAST_ERROR = ""

STUDIO_TO_EL = {
    "lumen": "cjVigY5qzO86Huf0OWal",
    "orion": "JBFqnCBsd6RMkjVDRZzb",
    "eve": "EXAVITQu4vr4xnSDxMaL",
    "ara": "FGY2WhTYpPnrIDTdsKH5",
    "perseus": "onwK4e9ZLuTAKqWW03F9",
    "celeste": "Xb7hH8MSUJpSbSDYk0k2",
    "leo": "nPczCjzI2devNBz1zQrb",
    "atlas": "iP95p4xoKVk53GoZ742B",
    "zenith": "IKne3meq5aSn9XLyUdCD",
    "zagan": "N2lVS1w4EtoT3dr4eOWO",
    "helios": "TX3LPaxmHKxFdv7VOQHJ",
    "carina": "hpp4J3VqNfWAUOO0d1Us",
    "aurora": "cgSgspJ2msm6clMCkdW9",
    "liora": "XrExE9yKIg1WjnnlVkGX",
    "luna": "SAz9YHcvj6GT2YYXdXww",
    "castor": "CwhRBWXzGAHq8TQ4Fs17",
    "rex": "pNInz6obpgDQGcFmaJgB",
}


def voice_id_for(voice_id: str) -> str:
    ident = (voice_id or "").strip()
    if ident.startswith("lumean:"):
        ident = ident[7:]
    elif ident.startswith("lumean-"):
        ident = ident[7:]
    if re.fullmatch(r"[A-Za-z0-9]{16,}", ident):
        return ident
    return STUDIO_TO_EL.get(ident.lower(), STUDIO_TO_EL["lumen"])


def unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and isinstance(payload.get("data"), (dict, list)):
        return payload["data"]
    return payload


def _request(
    method: str,
    path: str,
    api_key: str,
    *,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    timeout: int = 30,
) -> tuple[int, Any]:
    url = LUMEAN_BASE + path
    if query:
        qs = urllib.parse.urlencode({k: v for k, v in query.items() if v is not None and v != ""})
        if qs:
            url = f"{url}?{qs}"
    data = None
    headers = {"X-API-KEY": api_key, "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read().decode("utf-8")
            status = getattr(res, "status", 200)
            if not raw:
                return status, {}
            try:
                return status, json.loads(raw)
            except json.JSONDecodeError:
                return status, {"raw": raw}
    except urllib.error.HTTPError as err:
        raw = ""
        try:
            raw = err.read().decode("utf-8")
        except Exception:
            raw = ""
        try:
            return err.code, json.loads(raw) if raw else {"error": err.reason}
        except json.JSONDecodeError:
            return err.code, {"error": raw or str(err.reason)}
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        return 0, {"error": str(err)}


def list_library_voices(
    api_key: str,
    *,
    page: int = 0,
    page_size: int = 30,
    search: str = "",
    gender: str = "",
) -> dict[str, Any]:
    query: dict[str, Any] = {"page": max(0, int(page)), "page_size": max(1, min(50, int(page_size)))}
    if search.strip():
        query["search"] = search.strip()[:80]
    if gender in {"male", "female"}:
        query["gender"] = gender
    status, payload = _request("GET", "/voices/elevenlabs/library", api_key, query=query, timeout=12)
    data = unwrap(payload)
    if not isinstance(data, dict):
        data = {}
    voices = data.get("voices") if isinstance(data.get("voices"), list) else []
    if isinstance(payload, dict) and isinstance(payload.get("voices"), list) and not voices:
        voices = payload["voices"]
    flat: list[dict[str, Any]] = []
    for row in voices:
        if not isinstance(row, dict):
            continue
        labels = row.get("labels") if isinstance(row.get("labels"), dict) else {}
        merged = dict(row)
        for key in ("gender", "age", "accent", "use_case", "descriptive", "language"):
            if not merged.get(key) and labels.get(key):
                merged[key] = labels[key]
        if not merged.get("preview_url"):
            samples = row.get("samples") if isinstance(row.get("samples"), list) else []
            if samples and isinstance(samples[0], dict):
                merged["preview_url"] = samples[0].get("preview_url") or samples[0].get("url")
        flat.append(merged)
    return {
        "ok": status == 200,
        "status": status,
        "voices": flat,
        "total": int(data.get("total") or 0),
        "page": int(data.get("page") or page),
        "page_size": int(data.get("page_size") or page_size),
        "has_more": bool(data.get("has_more")),
        "error": None if status == 200 else (payload.get("error") if isinstance(payload, dict) else "failed"),
    }


def _cache_path() -> Path:
    from worker.env import data_root

    dest = data_root() / "cache"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / "lumean-templates.json"


def _read_cache() -> dict[str, str]:
    path = _cache_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items() if k and v}


def _write_cache(rows: dict[str, str]) -> None:
    path = _cache_path()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    tmp.replace(path)


def template_body(voice_id: str, name: str = "") -> dict[str, Any]:
    ident = voice_id_for(voice_id)
    return {
        "service_key": "elevenlabs",
        "name": (name or f"LumenCut {ident[:8]}").strip()[:80],
        "is_public": False,
        "config": {
            "tts_settings": {
                "mode": "mode_v1",
                "model_id": "eleven_multilingual_v2",
                "voice_id": ident,
                "advanced_voice_settings": True,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "use_speaker_boost": True,
                    "speed": 1.0,
                },
            }
        },
    }


def ensure_template(api_key: str, voice_id: str) -> str:
    ident = voice_id_for(voice_id)
    cache = _read_cache()
    cached = cache.get(ident)
    if cached:
        return cached
    status, payload = _request("POST", "/templates", api_key, body=template_body(ident), timeout=20)
    data = unwrap(payload)
    tid = ""
    if isinstance(data, dict):
        tid = str(data.get("id") or "")
    if status in {200, 201} and tid:
        cache[ident] = tid
        _write_cache(cache)
        return tid
    return ""


def _order_id(payload: Any) -> str:
    data = unwrap(payload)
    if isinstance(data, dict):
        return str(data.get("id") or "")
    return ""


def _order_status(payload: Any) -> str:
    data = unwrap(payload)
    if isinstance(data, dict):
        return str(data.get("status") or "").lower()
    return ""


def _file_paths(payload: Any) -> list[str]:
    data = unwrap(payload)
    if not isinstance(data, dict):
        return []
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    rows: list[Any] = []
    for key in ("files", "service_files"):
        val = result.get(key) if result else None
        if isinstance(val, list):
            rows.extend(val)
    items = data.get("items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            rf = item.get("result_file")
            if isinstance(rf, dict):
                rows.append(rf)
            elif isinstance(rf, str):
                rows.append(rf)
    out: list[str] = []
    for row in rows:
        if isinstance(row, str) and row.strip():
            out.append(row.strip())
        elif isinstance(row, dict):
            path = str(row.get("path") or row.get("url") or "").strip()
            if path:
                out.append(path)
    return out


def _download_url(api_key: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    status, payload = _request("POST", "/storage/url", api_key, body={"path": path}, timeout=20)
    data = unwrap(payload)
    if status == 200 and isinstance(data, dict):
        return str(data.get("url") or data.get("signed_url") or "")
    return ""


def _write_url(url: str, dest: Path) -> bool:
    if not url:
        return False
    req = urllib.request.Request(url, method="GET", headers={"Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            blob = res.read()
        if len(blob) < 400:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        return dest.is_file() and dest.stat().st_size > 400
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def speak_one(text: str, voice_id: str, api_key: str, dest: Path) -> tuple[float, list[dict]]:
    """Synthesize one paragraph. Returns (duration_sec, words). Words stay empty — caller aligns."""
    from worker.tts import probe_duration

    global LAST_ERROR
    LAST_ERROR = ""
    clean = (text or "").strip()[:LUMEAN_MAX_CHARS]
    if not clean or not api_key:
        LAST_ERROR = "empty text or missing LUMEAN_API_KEY"
        return 0.0, []
    template_id = ensure_template(api_key, voice_id)
    if not template_id:
        LAST_ERROR = "template create failed"
        return 0.0, []
    status, payload = _request(
        "POST",
        "/orders",
        api_key,
        body={"template_id": template_id, "input_text": clean},
        timeout=30,
    )
    order_id = _order_id(payload)
    if status not in {200, 201} or not order_id:
        LAST_ERROR = f"order HTTP {status}: {_err_text(payload)}"
        return 0.0, []
    last: Any = payload
    for _ in range(POLL_TRIES):
        st = _order_status(last)
        if st in {"completed", "complete", "done", "success", "partially_completed"}:
            break
        if st in {"failed", "error", "cancelled", "canceled"}:
            LAST_ERROR = f"order {st}: {_err_text(last)}"
            return 0.0, []
        time.sleep(POLL_SEC)
        _code, last = _request("GET", f"/orders/{order_id}", api_key, timeout=20)
    paths = _file_paths(last)
    for path in paths:
        url = _download_url(api_key, path)
        if _write_url(url, dest):
            return probe_duration(dest), []
    LAST_ERROR = f"no audio files on order {order_id}"
    return 0.0, []


def _err_text(payload: Any) -> str:
    if isinstance(payload, dict):
        return str(payload.get("error") or payload.get("message") or payload)[:180]
    return str(payload)[:180]
