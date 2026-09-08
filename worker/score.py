"""Noun-overlap scoring. CLIP (open_clip ViT-B-32 / ViT-L-14) when installed."""
from __future__ import annotations

import re
import threading
from typing import Iterable

STOP = {
    "the", "and", "that", "this", "with", "from", "were", "have", "been", "they",
    "their", "there", "which", "would", "could", "about", "into", "when", "what",
    "your", "them", "then", "than", "some", "more", "only", "over", "also", "just",
    "not", "was", "are", "for", "but", "you", "had", "its", "his", "her", "she",
    "him", "who", "did", "does", "very", "still", "even", "most", "many", "each",
    "same", "both", "such", "those", "these", "after", "before", "because",
    "это", "как", "что", "для", "или", "его", "ее", "они", "мы", "на", "по", "из",
    "не", "но", "же", "бы", "то", "за", "от", "до", "при", "был", "была", "были",
}

HARD_PRODUCT = {
    "box", "kit", "bottle", "flask", "thermos", "pail", "tin", "latch", "lid",
    "lunchbox", "handle", "stamp", "vacuum", "liner", "cup",
}

PRODUCT_SYN = {
    "kit": ["kit", "box", "pail", "lunchbox"],
    "box": ["box", "kit", "pail", "lunchbox"],
    "lunchbox": ["lunchbox", "box", "kit"],
    "bottle": ["bottle", "flask", "thermos"],
    "flask": ["flask", "bottle", "thermos"],
    "thermos": ["thermos", "flask", "bottle"],
    "pail": ["pail", "box", "kit"],
    "tin": ["tin", "steel", "metal"],
}

JUNK = re.compile(r"logo|icon|ambox|flag|symbol|disambig|wiki|placeholder|default|ogg|pdf|svg|map\b|coat of arms", re.I)

_CLIP = None
_CLIP_NAME = ""
_CLIP_LOCK = threading.Lock()
CLIP_QUALITY = False


def nouns(text: str) -> list[str]:
    words = re.sub(r"[^a-zа-яё0-9\s-]", " ", text.lower())
    return [w for w in words.split() if len(w) >= 3 and w not in STOP]


def overlap(haystack: str, needle: str) -> float:
    query = nouns(needle)
    title = nouns(haystack)
    if not query:
        return 0.0
    hits = 0
    for word in query:
        if any(x == word or (len(word) >= 4 and (word in x or x in word)) for x in title):
            hits += 1
    return hits / len(query)


def product_match(word: str, title_nouns: Iterable[str]) -> bool:
    alts = PRODUCT_SYN.get(word, [word])
    title = list(title_nouns)
    return any(any(x == a or a in x or x in a for x in title) for a in alts)


def score_visual(title: str, query: str, kind: str = "") -> float:
    s = overlap(title, query)
    q_prod = [w for w in nouns(query) if w in HARD_PRODUCT]
    t = nouns(title)
    if q_prod:
        hits = sum(1 for w in q_prod if product_match(w, t))
        if hits == 0:
            s -= 0.5
        else:
            s += 0.3 * (hits / len(q_prod))
    if kind == "action" and re.search(r"hands|opening|pour|walk|street", title, re.I):
        s += 0.15
    if kind == "dialogue" and re.search(r"portrait|face|person|man|woman", title, re.I):
        s += 0.2
    if kind == "abstraction" and re.search(r"texture|light|window|empty", title, re.I):
        s += 0.12
    if re.search(r"portrait|album|trailer|poster|headshot|selfie|mugshot", title, re.I) and kind != "dialogue":
        s -= 0.35
    return s


def is_junk(title: str, src: str = "") -> bool:
    return bool(JUNK.search(title) or JUNK.search(src))


def clip_available() -> bool:
    try:
        import open_clip  # noqa: F401
        import torch  # noqa: F401
        from PIL import Image  # noqa: F401
        return True
    except Exception:
        return False


def set_clip_quality(quality: bool) -> None:
    global CLIP_QUALITY, _CLIP, _CLIP_NAME
    CLIP_QUALITY = bool(quality)
    want = "ViT-L-14" if CLIP_QUALITY else "ViT-B-32"
    if _CLIP is not None and _CLIP_NAME != want:
        _CLIP = None
        _CLIP_NAME = ""


def _load_clip():
    global _CLIP, _CLIP_NAME
    if _CLIP is not None:
        return _CLIP
    import open_clip
    import torch

    name = "ViT-L-14" if CLIP_QUALITY else "ViT-B-32"
    model, _, preprocess = open_clip.create_model_and_transforms(name, pretrained="openai")
    tokenizer = open_clip.get_tokenizer(name)
    model.eval()
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
        model = model.to(device)
    _CLIP = (model, preprocess, tokenizer, device, torch)
    _CLIP_NAME = name
    return _CLIP


def clip_score(image_path: str, query: str | list[str]) -> float | None:
    """Cosine similarity, max over query texts. None if open_clip is not installed."""
    if not clip_available():
        return None
    texts = [t for t in (query if isinstance(query, list) else [query]) if str(t).strip()]
    if not texts:
        return None
    try:
        from PIL import Image

        with _CLIP_LOCK:
            model, preprocess, tokenizer, device, torch = _load_clip()
            image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
            tokens = tokenizer(texts)
            if hasattr(tokens, "to"):
                tokens = tokens.to(device)
            with torch.no_grad():
                image_features = model.encode_image(image)
                text_features = model.encode_text(tokens)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                sims = (image_features @ text_features.T).squeeze(0)
                return float(sims.max().item() if hasattr(sims, "max") else sims)
    except Exception:
        return None
