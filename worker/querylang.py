"""English stock-search queries from phrase meaning + brand context. Never a translation of the VO."""
from __future__ import annotations

import re
from typing import Any, Iterable

CYR = re.compile(r"[а-яё]", re.I)
LAT = re.compile(r"[a-z]", re.I)
YEAR = re.compile(r"\b((?:19|20)\d{2})s?\b")
STOP = {
    "the", "and", "that", "this", "with", "from", "were", "have", "been", "they", "their",
    "for", "but", "you", "had", "its", "his", "her", "she", "him", "who", "did", "a", "an",
    "of", "to", "in", "on", "at", "or", "if", "as", "by", "it", "be", "we", "is",
    "это", "как", "для", "что", "они", "она", "он", "был", "была", "были", "еще", "ещё",
}

LEXICON: list[tuple[str, str]] = sorted(
    [
        ("школьн", "school"),
        ("школ", "school"),
        ("обед", "school dinner"),
        ("ужин", "dinner"),
        ("вечерн", "evening"),
        ("столов", "canteen"),
        ("поднос", "tray"),
        ("эмаль", "enamel"),
        ("эмалир", "enamel"),
        ("кухн", "kitchen"),
        ("кастрюл", "saucepan"),
        ("чайник", "kettle"),
        ("пудинг", "pudding"),
        ("заварн", "custard"),
        ("молочн", "milk"),
        ("хлеб", "bread"),
        ("мяс", "meat"),
        ("рыб", "fish"),
        ("картофел", "potato"),
        ("картош", "potato"),
        ("британ", "British"),
        ("англич", "English"),
        ("англи", "England"),
        ("лондон", "London"),
        ("завод", "factory"),
        ("фабрик", "factory"),
        ("цех", "workshop"),
        ("сталь", "steel"),
        ("металл", "metal"),
        ("ржав", "rust"),
        ("коридор", "corridor"),
        ("класс", "classroom"),
        ("учитель", "teacher"),
        ("учен", "pupil"),
        ("детей", "children"),
        ("дети", "children"),
        ("ребён", "child"),
        ("ребен", "child"),
        ("очеред", "queue"),
        ("паровоз", "steam train"),
        ("поезд", "train"),
        ("платформ", "platform"),
        ("вокзал", "railway station"),
        ("письм", "letter"),
        ("фотограф", "photograph"),
        ("архив", "archive"),
        ("войн", "war"),
        ("солдат", "soldier"),
        ("улиц", "street"),
        ("город", "town"),
        ("деревн", "village"),
        ("ферм", "farm"),
        ("поле", "field"),
        ("снег", "snow"),
        ("туман", "fog"),
        ("пар", "steam"),
        ("окно", "window"),
        ("окон", "window"),
        ("дверь", "door"),
        ("стул", "chair"),
        ("стол", "table"),
        ("коробк", "tin"),
        ("ланчбокс", "lunch box"),
        ("термос", "flask"),
        ("бутылк", "bottle"),
        ("чашк", "mug"),
        ("тарелк", "plate"),
        ("ложк", "spoon"),
        ("вилк", "fork"),
        ("ностальг", "nostalgia"),
        ("памят", "memory"),
        ("поколени", "generation"),
        ("семейн", "family"),
        ("матер", "mother"),
        ("отец", "father"),
        ("бабушк", "grandmother"),
        ("дедушк", "grandfather"),
        ("1970", "1970s"),
        ("семидесят", "1970s"),
        ("восьмидесят", "1980s"),
        ("шестидесят", "1960s"),
    ],
    key=lambda row: len(row[0]),
    reverse=True,
)

THEME_TAGS = {
    "history": ["archive", "documentary"],
    "crime": ["crime documentary", "archive"],
    "nature": ["nature documentary"],
    "tech": ["technology documentary"],
    "modern": ["documentary still"],
    "warm": ["analog photograph"],
}

PLACE_HINTS = (
    (re.compile(r"british|britain|uk\b|england|англий|британ", re.I), "British"),
    (re.compile(r"school|школ|canteen|столов|dinner|обед|ужин", re.I), "school canteen"),
    (re.compile(r"1970|70s|семидесят", re.I), "1970s"),
    (re.compile(r"amish", re.I), "Amish"),
    (re.compile(r"factory|завод|фабрик", re.I), "factory"),
)


def is_english_query(text: str) -> bool:
    ru = len(CYR.findall(text or ""))
    en = len(LAT.findall(text or ""))
    if ru and ru > en:
        return False
    return True


def era_token(text: str) -> str | None:
    m = YEAR.search(text or "")
    if not m:
        return None
    if m.group(0).lower().endswith("s"):
        return m.group(0)
    return f"{(int(m.group(1)) // 10) * 10}s"


def map_token(word: str) -> str | None:
    w = (word or "").lower()
    if not w or w in STOP:
        return None
    if LAT.search(w) and not CYR.search(w):
        return w if len(w) >= 3 else None
    for stem, eng in LEXICON:
        if w.startswith(stem):
            return eng
    return None


def meaning_terms(text: str) -> list[str]:
    bits = re.sub(r"[^a-zа-яё0-9\s-]", " ", (text or "").lower())
    out: list[str] = []
    seen: set[str] = set()
    for w in bits.split():
        mapped = map_token(w)
        if not mapped:
            continue
        key = mapped.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(mapped)
        if len(out) == 8:
            break
    return out


def brand_context(scenes: dict[str, Any] | None) -> list[str]:
    src = scenes or {}
    blob = " ".join(
        str(src.get(k) or "")
        for k in ("scriptNotes", "scriptStyle", "title", "brandName", "themeId", "exampleScript")
    )
    tags: list[str] = []
    for rx, label in PLACE_HINTS:
        if rx.search(blob):
            tags.append(label)
    tags.extend(THEME_TAGS.get(str(src.get("themeId") or ""), []))
    return _unique(tags)


def _join_unique(*parts: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        for w in str(part or "").split():
            key = w.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(w)
    return " ".join(out)


def stock_queries(text: str, *, era: str | None = None, context: Iterable[str] | None = None) -> list[str]:
    terms = meaning_terms(text)
    ctx = [str(c).strip() for c in (context or []) if str(c).strip()]
    decade = era or era_token(text) or next((c for c in ctx if re.match(r"(?:19|20)\d{0,2}s$", c)), "")
    place = next((c for c in ctx if c[:1].isupper() or c.lower() in {"british", "english"}), "")
    extra = [c for c in ctx if c not in {decade, place}]
    obj = " ".join(terms[:4]) or "documentary still"
    raw = [
        _join_unique(decade, place, obj),
        _join_unique(place, obj, "archive photograph"),
        _join_unique(obj, *extra[:2], "documentary still"),
        _join_unique(obj, "16:9 photograph"),
    ]
    out: list[str] = []
    for q in raw:
        q = re.sub(r"\s+", " ", q).strip()[:90]
        if not q or not is_english_query(q):
            continue
        if q not in out:
            out.append(q)
        if len(out) == 4:
            break
    if len(out) < 2:
        fallback = " ".join(p for p in (decade, place, "documentary archive photograph") if p)[:90]
        if fallback and fallback not in out:
            out.append(fallback)
    return out[:4]


def _unique(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for row in rows:
        key = row.lower()
        if not row or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out
