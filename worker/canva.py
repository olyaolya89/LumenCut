"""Canva-inspired YouTube packs. Applied locally; Connect API is optional."""
from __future__ import annotations

from typing import Any

PACKS: dict[str, dict[str, Any]] = {
    "canva-bold-yt": {
        "themeId": "modern",
        "color": "#e11d48",
        "backgroundId": "ink",
        "avgShot": 2.4,
        "photoShare": 0.35,
        "plaqueRate": 0.72,
        "titles": "bold caps",
        "grade": "kodak",
    },
    "canva-pastel": {
        "themeId": "minimal",
        "color": "#ec4899",
        "backgroundId": "mist",
        "avgShot": 4.2,
        "photoShare": 0.7,
        "plaqueRate": 0.28,
        "titles": "sentence case",
        "grade": "polaroid",
    },
    "canva-editorial": {
        "themeId": "history",
        "color": "#1c1917",
        "backgroundId": "linen",
        "avgShot": 3.8,
        "photoShare": 0.55,
        "plaqueRate": 0.48,
        "titles": "serif headline",
        "grade": "vintage",
    },
    "canva-neon": {
        "themeId": "modern",
        "color": "#22d3ee",
        "backgroundId": "void",
        "avgShot": 2.2,
        "photoShare": 0.3,
        "plaqueRate": 0.64,
        "titles": "neon lower-third",
        "grade": "cool",
    },
    "canva-amber-doc": {
        "themeId": "standard",
        "color": "#d97706",
        "backgroundId": "grid",
        "avgShot": 3.2,
        "photoShare": 0.42,
        "plaqueRate": 0.52,
        "titles": "condensed caption",
        "grade": "noir",
    },
    "canva-cream": {
        "themeId": "history",
        "color": "#b45309",
        "backgroundId": "paper",
        "avgShot": 4.0,
        "photoShare": 0.62,
        "plaqueRate": 0.4,
        "titles": "lecture title",
        "grade": "vintage",
    },
    "canva-corporate": {
        "themeId": "minimal",
        "color": "#3b6cff",
        "backgroundId": "slate",
        "avgShot": 3.6,
        "photoShare": 0.5,
        "plaqueRate": 0.32,
        "titles": "plain statement",
        "grade": "none",
    },
    "canva-crime": {
        "themeId": "crime",
        "color": "#e23a3a",
        "backgroundId": "ember",
        "avgShot": 2.8,
        "photoShare": 0.38,
        "plaqueRate": 0.58,
        "titles": "case file",
        "grade": "noir",
    },
}


def pack_of(style_id: str | None) -> dict[str, Any] | None:
    ident = (style_id or "").strip()
    return PACKS.get(ident)


def apply_canva_style(scenes: dict[str, Any]) -> dict[str, Any]:
    """Fill theme/colour/editing from a Canva pack when the brand picked one."""
    pack = pack_of(str(scenes.get("canvaStyleId") or ""))
    if not pack:
        return scenes
    next_scenes = dict(scenes)
    if not next_scenes.get("themeId"):
        next_scenes["themeId"] = pack["themeId"]
    if not next_scenes.get("brandColor"):
        next_scenes["brandColor"] = pack["color"]
    if not next_scenes.get("backgroundId"):
        next_scenes["backgroundId"] = pack["backgroundId"]
    style = dict(next_scenes.get("editingStyle") or {})
    for key in ("avgShot", "photoShare", "plaqueRate", "titles", "grade"):
        if style.get(key) in (None, ""):
            style[key] = pack[key]
    next_scenes["editingStyle"] = style
    if next_scenes.get("graphicsDensity") is None:
        next_scenes["graphicsDensity"] = pack["plaqueRate"]
    return next_scenes
