"""Compatibility wrappers for the deprecated ``quarry.inspector`` API."""

from __future__ import annotations

from collections import Counter
from typing import Any

from bs4 import BeautifulSoup, Tag

from quarry.framework_profiles import (
    detect_framework,
    get_framework_field_selector,
    is_framework_pattern,
)
from quarry.lib.bs4_utils import attr_str
from quarry.tools.scout.analyzer import _suggest_fields, analyze_page


def _class_tokens(tag: Tag) -> list[str]:
    raw = tag.get("class")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [c for c in raw if isinstance(c, str)]


def inspect_html(html: str) -> dict[str, Any]:
    """Return high-level metadata for legacy callers."""

    if not html or not html.strip():
        return {
            "title": "",
            "description": "",
            "total_links": 0,
            "repeated_classes": [],
            "sample_links": [],
        }

    analysis = analyze_page(html)
    soup = BeautifulSoup(html, "html.parser")

    metadata = analysis.get("metadata", {})

    class_counter: Counter[str] = Counter()
    samples: dict[str, Tag] = {}
    for tag in soup.find_all(True):
        for cls in _class_tokens(tag):
            class_counter[cls] += 1
            samples.setdefault(cls, tag)

    repeated_classes: list[dict[str, Any]] = []
    for cls, count in class_counter.most_common(20):
        if count < 3:
            continue
        sample = samples.get(cls)
        repeated_classes.append(
            {
                "class": cls,
                "count": count,
                "tag": sample.name if sample else None,
                "sample_text": (sample.get_text(strip=True)[:100] if sample else ""),
            }
        )

    sample_links = []
    for link in soup.find_all("a", href=True)[:10]:
        sample_links.append(
            {
                "href": link.get("href") or "",
                "text": link.get_text(strip=True),
                "class": " ".join(_class_tokens(link)),
            }
        )

    return {
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "total_links": len(soup.find_all("a", href=True)),
        "repeated_classes": repeated_classes,
        "sample_links": sample_links,
        "containers": analysis.get("containers", []),
    }


def find_item_selector(html: str, min_items: int = 3) -> list[dict[str, Any]]:
    """Approximate the legacy selector suggestions using Scout containers."""

    if not html or not html.strip():
        return []

    analysis = analyze_page(html)
    soup = BeautifulSoup(html, "html.parser")

    containers = analysis.get("containers") or []
    detected_framework = detect_framework(html)

    results: list[dict[str, Any]] = []

    for entry in containers:
        count = entry.get("item_count", 0)
        if count < min_items:
            continue

        selector = entry.get("child_selector") or entry.get("selector")
        if not selector:
            continue

        score = entry.get("content_score", 0)
        if score >= 70:
            confidence = "very_high"
        elif score >= 50:
            confidence = "high"
        elif score >= 30:
            confidence = "medium"
        else:
            confidence = "low"

        sample_text = entry.get("sample_text", "")
        sample_url = ""

        try:
            element = soup.select_one(selector)
        except Exception:
            element = None

        if element:
            link = element.find("a", href=True)
            if link:
                sample_url = attr_str(link, "href")
                if not sample_text:
                    sample_text = link.get_text(strip=True)
            if not sample_text:
                sample_text = element.get_text(strip=True)

        framework_match = False
        if detected_framework:
            framework_match = is_framework_pattern(selector, detected_framework)

        results.append(
            {
                "selector": selector,
                "count": count,
                "sample_title": sample_text[:120],
                "sample_url": sample_url,
                "confidence": confidence,
                "framework_match": framework_match,
            }
        )

    return results


def generate_field_selector(item_element: Tag, field_type: str) -> str | None:
    """Suggest a field selector for ``item_element``."""

    if not isinstance(item_element, Tag):
        return None

    framework = detect_framework(str(item_element.parent or item_element), item_element)
    if framework:
        selector = get_framework_field_selector(framework, item_element, field_type)
        if isinstance(selector, str) and selector:
            return selector

    normalized_field = field_type.lower()
    candidates = _suggest_fields(item_element)

    def _format(candidate: dict[str, Any]) -> str | None:
        selector_val = candidate.get("selector")
        if not isinstance(selector_val, str) or not selector_val:
            return None
        attribute_val = candidate.get("attribute")
        if isinstance(attribute_val, str) and "::attr" not in selector_val:
            return f"{selector_val}::attr({attribute_val})"
        return selector_val

    for candidate in candidates:
        name = (candidate.get("name") or "").lower()
        if name == normalized_field:
            formatted = _format(candidate)
            if formatted:
                return formatted

    aliases = {
        "url": {"link", "href"},
        "title": {"heading", "name"},
        "author": {"byline", "creator"},
        "date": {"time", "published", "posted"},
    }

    for candidate in candidates:
        name = (candidate.get("name") or "").lower()
        for target, variants in aliases.items():
            if normalized_field == target and name in variants:
                formatted = _format(candidate)
                if formatted:
                    return formatted

    # Lightweight fallbacks when patterns didn't produce a direct match
    try:
        if normalized_field == "title":
            heading_el: Tag | None = item_element.select_one("a, h1, h2, h3, h4")
            if heading_el is not None:
                return "a" if heading_el.name == "a" else (heading_el.name or None)
            # Fallback to any container with a class containing 'title'
            if item_element.select_one('[class*="title"]'):
                return '[class*="title"]'
        if normalized_field == "date":
            if item_element.select_one("[data-date]"):
                return "[data-date]"
            if item_element.select_one("time[datetime], time"):
                return "time[datetime]" if item_element.select_one("time[datetime]") else "time"
        if normalized_field == "author":
            if item_element.select_one("[data-author]"):
                return "[data-author]"
        if normalized_field == "score":
            if item_element.select_one("[data-score]"):
                return "[data-score]"
    except Exception:
        pass

    return None


def preview_extraction(
    html: str,
    item_selector: str,
    field_selectors: dict[str, str],
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Preview extracted records for a selector map (legacy helper)."""

    if not html or not html.strip() or not item_selector or not item_selector.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    try:
        items = soup.select(item_selector)
    except Exception:
        return []

    if not items:
        return []

    previews: list[dict[str, Any]] = []

    for item in items[:limit]:
        record: dict[str, Any] = {}
        for field_name, sel in field_selectors.items():
            selector = (sel or "").strip()
            if not selector:
                record[field_name] = ""
                continue

            try:
                if "::attr(" in selector:
                    css, attr_part = selector.split("::attr(", 1)
                    attr = attr_part.rstrip(")")
                    target = item if not css else item.select_one(css)
                    record[field_name] = target.get(attr, "") if target else ""
                else:
                    target = item.select_one(selector)
                    record[field_name] = target.get_text(strip=True) if target else ""
            except Exception:
                record[field_name] = "[extraction failed]"
        previews.append(record)

    return previews


__all__ = [
    "find_item_selector",
    "generate_field_selector",
    "inspect_html",
    "preview_extraction",
]
