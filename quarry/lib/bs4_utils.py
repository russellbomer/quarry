from __future__ import annotations

from bs4 import BeautifulSoup, ResultSet, Tag


def class_tokens(tag: Tag) -> list[str]:
    raw = tag.get("class")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [c for c in raw if isinstance(c, str)]


def attr_str(tag: Tag, name: str) -> str:
    value = tag.get(name)
    return value if isinstance(value, str) else ""


def select_list(node: BeautifulSoup | Tag, selector: str) -> list[Tag]:
    try:
        result = node.select(selector)
    except Exception:
        return []
    if isinstance(result, ResultSet):
        # Convert ResultSet[Tag] to list[Tag]
        return list(result)
    return list(result)
