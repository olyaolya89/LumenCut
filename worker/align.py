"""Word timestamps: ElevenLabs characters, Whisper words, script alignment."""
from __future__ import annotations

import difflib
import re
from typing import Any

TOKEN_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text or "")


def norm_token(token: str) -> str:
    return re.sub(r"[^\w]+", "", token or "", flags=re.UNICODE).lower()


def chars_to_words(
    characters: list[str] | None,
    starts: list[float] | None,
    ends: list[float] | None,
) -> list[dict[str, Any]]:
    """ElevenLabs character alignment → word rows with millisecond bounds."""
    chars = list(characters or [])
    st = list(starts or [])
    en = list(ends or [])
    n = min(len(chars), len(st), len(en))
    words: list[dict[str, Any]] = []
    buf: list[str] = []
    s0: float | None = None
    e0: float | None = None
    for i in range(n):
        ch = chars[i]
        if str(ch).isspace():
            if buf and s0 is not None and e0 is not None:
                words.append(
                    {
                        "w": "".join(buf),
                        "startMs": int(float(s0) * 1000),
                        "endMs": max(int(float(s0) * 1000) + 40, int(float(e0) * 1000)),
                    }
                )
                buf, s0, e0 = [], None, None
            continue
        if s0 is None:
            s0 = st[i]
        buf.append(str(ch))
        e0 = en[i]
    if buf and s0 is not None and e0 is not None:
        words.append(
            {
                "w": "".join(buf),
                "startMs": int(float(s0) * 1000),
                "endMs": max(int(float(s0) * 1000) + 40, int(float(e0) * 1000)),
            }
        )
    return words


def even_words(tokens: list[str], duration_ms: int) -> list[dict[str, Any]]:
    if not tokens:
        return []
    weights = [max(1, len(t)) for t in tokens]
    total = sum(weights) or 1
    span = max(1, int(duration_ms))
    cursor = 0
    rows: list[dict[str, Any]] = []
    for i, tok in enumerate(tokens):
        nxt = span if i == len(tokens) - 1 else cursor + max(40, int(span * weights[i] / total))
        rows.append({"w": tok, "startMs": cursor, "endMs": max(cursor + 40, nxt)})
        cursor = rows[-1]["endMs"]
    return rows


def scale_words(words: list[dict[str, Any]], factor: float) -> list[dict[str, Any]]:
    if abs(factor - 1.0) < 0.002:
        return words
    out = []
    for w in words:
        row = dict(w)
        row["startMs"] = int(round(int(w.get("startMs") or 0) * factor))
        row["endMs"] = max(row["startMs"] + 40, int(round(int(w.get("endMs") or 0) * factor)))
        out.append(row)
    return out


def align_words(script_tokens: list[str], spoken: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map ASR/TTS timed words onto script tokens with difflib (custom audio + punctuation drift)."""
    if not script_tokens:
        return []
    if not spoken:
        return even_words(script_tokens, max(400, 180 * len(script_tokens)))

    a = [norm_token(str(w.get("w") or "")) for w in spoken]
    b = [norm_token(t) for t in script_tokens]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out: list[dict[str, Any] | None] = [None] * len(script_tokens)

    def spoken_at(i: int) -> dict[str, Any]:
        return spoken[max(0, min(i, len(spoken) - 1))]

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in {"equal", "replace"}:
            span_a = max(0, i2 - i1)
            span_b = max(0, j2 - j1)
            for k in range(span_b):
                if span_a <= 0:
                    src = spoken_at(i1)
                elif span_b >= span_a:
                    src = spoken_at(i1 + min(k, span_a - 1))
                else:
                    src = spoken_at(i1 + int(k * span_a / span_b))
                out[j1 + k] = {
                    "w": script_tokens[j1 + k],
                    "startMs": int(src.get("startMs") or 0),
                    "endMs": int(src.get("endMs") or 0),
                }
            if tag == "replace" and span_a > 0 and span_b > 0:
                last = out[j2 - 1]
                if last:
                    last["endMs"] = int(spoken_at(i2 - 1).get("endMs") or last["endMs"])
                    if span_b == 1:
                        last["startMs"] = int(spoken[i1].get("startMs") or last["startMs"])
        elif tag == "insert":
            prev_end = int(spoken[i1 - 1].get("endMs") or 0) if i1 > 0 else int(spoken[0].get("startMs") or 0)
            next_start = int(spoken[i1].get("startMs") or prev_end + 200) if i1 < len(spoken) else prev_end + 200 * (j2 - j1)
            span = max(1, next_start - prev_end)
            n = max(1, j2 - j1)
            for k in range(n):
                s = prev_end + int(span * k / n)
                e = prev_end + int(span * (k + 1) / n)
                out[j1 + k] = {"w": script_tokens[j1 + k], "startMs": s, "endMs": max(s + 40, e)}
        elif tag == "delete":
            if j1 > 0 and out[j1 - 1] is not None and i2 > i1:
                out[j1 - 1]["endMs"] = int(spoken_at(i2 - 1).get("endMs") or 0)

    last_t = 0
    filled: list[dict[str, Any]] = []
    for i, row in enumerate(out):
        if row is None:
            nxt = next((o for o in out[i + 1 :] if o is not None), None)
            end = int(nxt["startMs"]) if nxt else last_t + 200
            row = {"w": script_tokens[i], "startMs": last_t, "endMs": max(last_t + 40, end)}
        if row["endMs"] <= row["startMs"]:
            row["endMs"] = row["startMs"] + 40
        last_t = int(row["endMs"])
        filled.append(row)

    cursor = 0
    for row in filled:
        if row["startMs"] < cursor:
            row["startMs"] = cursor
        if row["endMs"] <= row["startMs"]:
            row["endMs"] = row["startMs"] + 40
        cursor = int(row["endMs"])
    return filled


def words_for_script(
    phrases: list[dict[str, Any]],
    spoken: list[dict[str, Any]] | None,
    duration_ms: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Align spoken words to phrases. Scene bounds come from first/last word."""
    script_tokens: list[str] = []
    owners: list[int] = []
    for i, phrase in enumerate(phrases):
        toks = tokenize(phrase.get("text") or "")
        if not toks:
            toks = [(phrase.get("text") or "").strip() or "…"]
        script_tokens.extend(toks)
        owners.extend([i] * len(toks))

    aligned = align_words(script_tokens, spoken or []) if spoken else even_words(script_tokens, max(1, duration_ms))
    buckets: list[list[dict[str, Any]]] = [[] for _ in phrases]
    for word, owner in zip(aligned, owners):
        sid = phrases[owner].get("id")
        para = phrases[owner].get("paragraph")
        row = dict(word)
        if sid:
            row["sceneId"] = sid
        if para is not None:
            row["paragraph"] = para
        buckets[owner].append(row)

    timed: list[dict[str, Any]] = []
    cursor_ms = 0
    for i, phrase in enumerate(phrases):
        row = dict(phrase)
        words = buckets[i]
        if words:
            start_ms = int(words[0]["startMs"])
            end_ms = int(words[-1]["endMs"])
            if end_ms <= start_ms:
                end_ms = start_ms + 400
            row["startSec"] = round(start_ms / 1000, 3)
            row["durationSec"] = round(max(0.4, (end_ms - start_ms) / 1000), 3)
            row["words"] = words
            cursor_ms = end_ms
        else:
            dur = max(1.2, float(row.get("durationSec") or 2))
            start_ms = cursor_ms
            end_ms = start_ms + int(dur * 1000)
            guessed = even_words(tokenize(row.get("text") or "") or ["…"], end_ms - start_ms)
            for w in guessed:
                w["startMs"] = int(w["startMs"]) + start_ms
                w["endMs"] = int(w["endMs"]) + start_ms
                if row.get("id"):
                    w["sceneId"] = row["id"]
            row["startSec"] = round(start_ms / 1000, 3)
            row["durationSec"] = round((end_ms - start_ms) / 1000, 3)
            row["words"] = guessed
            cursor_ms = end_ms
        timed.append(row)

    flat = [w for p in timed for w in (p.get("words") or [])]
    return timed, flat
