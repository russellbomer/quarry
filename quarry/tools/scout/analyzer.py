"""Core analysis engine for Probe tool."""

import re
from collections import Counter
from typing import Any, cast

from bs4 import BeautifulSoup, Tag

from quarry.framework_profiles import _get_element_classes, detect_all_frameworks
from quarry.lib.selectors import build_robust_selector, simplify_selector


# Module-level helpers to normalize BeautifulSoup attributes
def _class_tokens(tag: Tag) -> list[str]:
    raw = tag.get("class")
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [c for c in raw if isinstance(c, str)]


def _attr_str(tag: Tag, name: str) -> str:
    value = tag.get(name)
    return value if isinstance(value, str) else ""


def analyze_page(html: str, url: str | None = None) -> dict[str, Any]:
    """
    Analyze a web page and return comprehensive structural analysis.

    Args:
        html: HTML content to analyze
        url: Optional URL for context

    Returns:
        Dictionary with analysis results:
        {
            "url": str,
            "frameworks": [...],      # Detected frameworks
            "containers": [...],      # Potential item containers
            "metadata": {...},        # Title, description, etc.
            "statistics": {...},      # Page stats
            "suggestions": {...}      # Extraction hints
        }
    """
    if not html or not html.strip():
        return {
            "url": url,
            "frameworks": [],
            "containers": [],
            "metadata": {},
            "statistics": {},
            "suggestions": {},
        }

    soup = BeautifulSoup(html, "html.parser")

    # Detect frameworks
    frameworks = _detect_all_frameworks(html)

    # Find containers (repeated item patterns)
    containers = _find_containers(soup)

    # Extract metadata
    metadata = _extract_metadata(soup)

    # Calculate statistics
    statistics = _calculate_statistics(soup)

    # Generate suggestions
    suggestions = _generate_suggestions(soup, containers, frameworks)

    return {
        "url": url,
        "frameworks": frameworks,
        "containers": containers,
        "metadata": metadata,
        "statistics": statistics,
        "suggestions": suggestions,
    }


def _detect_all_frameworks(html: str) -> list[dict[str, Any]]:
    """Detect all frameworks in the HTML."""
    frameworks = []

    # Parse HTML once for framework detection
    soup = BeautifulSoup(html, "html.parser")

    # Use existing framework detection
    body = soup.find("body") or soup
    detected = detect_all_frameworks(html, item_element=body)

    for profile_class, score in detected:
        # Get framework name from class
        framework_name = profile_class.__name__.replace("Profile", "").lower()

        # Get version if available
        version = None
        if hasattr(profile_class, "get_version"):
            try:
                version = profile_class.get_version(html)
            except Exception:
                pass

        # Calculate confidence (score is 0-100)
        confidence = min(score / 100.0, 1.0)

        frameworks.append(
            {
                "name": framework_name,
                "confidence": confidence,
                "version": version,
                "score": score,
            }
        )

    # Sort by confidence (already sorted by detect_all_frameworks)
    frameworks.sort(key=lambda x: cast(float, x.get("confidence", 0.0)), reverse=True)

    return frameworks


def _find_containers(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Find container elements with repeated children (likely item lists)."""
    containers = []

    # Blacklist of common boilerplate selectors/classes that should be deprioritized
    BOILERPLATE_PATTERNS = [
        'header',
        'footer',
        'nav',
        'menu',
        'sidebar',
        'breadcrumb',
        'cookie',
        'banner',
        'ad',
        'advertisement',
        'social',
        'share',
        'toolbar',
        'utility',
        'meta',
        'promo',
        'related',
        'widget',
        'plugin',
        'tracking',
    ]

    # Prioritize content containers
    CONTENT_PATTERNS = [
        'article',
        'post',
        'story',
        'item',
        'card',
        'entry',
        'product',
        'result',
        'listing',
        'content',
        'main',
        'feed',
        'list',
    ]

    # --- Safe attribute helpers moved to module scope ---

    def is_boilerplate(element: Tag) -> bool:
        """Check if element is likely boilerplate."""
        classes = _get_element_classes(element).lower()
        elem_id = _attr_str(element, "id").lower()
        combined = f"{classes} {elem_id}"

        return any(pattern in combined for pattern in BOILERPLATE_PATTERNS)

    def is_content_container(element: Tag) -> bool:
        """Check if element is likely a content container."""
        classes = _get_element_classes(element).lower()
        elem_id = _attr_str(element, "id").lower()
        combined = f"{classes} {elem_id}"

        return any(pattern in combined for pattern in CONTENT_PATTERNS)

    def has_meaningful_content(element: Tag) -> bool:
        """Heuristic: consider content meaningful if it has readable text or links."""
        text = element.get_text(strip=True)
        if element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            return True
        # Permit shorter items if there's at least some text or a link
        if len(text) >= 4:
            return True
        if element.find('a') and len(text) >= 5:
            return True
        return False

    for container_tag in [
        "body",
        "div",
        "section",
        "article",
        "ul",
        "ol",
        "main",
        "aside",
        "table",
        "tbody",
    ]:
        for container in soup.find_all(container_tag):
            # Skip obvious boilerplate
            if is_boilerplate(container):
                continue

            children = list(container.find_all(recursive=False))

            if len(children) >= 3:  # At least 3 items
                # Check if children are similar (same tag)
                child_tags = [c.name for c in children if hasattr(c, 'name')]
                if not child_tags:
                    continue

                tag_counts = Counter(child_tags)
                most_common_tag, count = tag_counts.most_common(1)[0]

                # If most children share same tag, it's a good container
                if count >= 3:
                    # Get the actual children with that tag
                    similar_children = [
                        c for c in children if hasattr(c, 'name') and c.name == most_common_tag
                    ]

                    # Prefer meaningful children, but allow large repeated sets
                    meaningful_children = [c for c in similar_children if has_meaningful_content(c)]
                    if len(meaningful_children) < 3 and count < 10:
                        continue

                    selector = build_robust_selector(container)
                    # Prefer a class-based child selector when a stable class is shared
                    child_selector = f"{selector} > {most_common_tag}"
                    shared_class = None
                    class_counts: Counter[str] = Counter()
                    for ch in similar_children:
                        for cls in _class_tokens(ch):
                            if _is_stable_css_token(cls):
                                class_counts[cls] += 1
                    if class_counts:
                        top_cls, top_count = class_counts.most_common(1)[0]
                        if top_count >= 3 and top_count >= max(3, int(len(similar_children) * 0.6)):
                            shared_class = top_cls
                    # If no shared class on the similar children, look at their immediate children
                    if not shared_class:
                        desc_class_counts: Counter[str] = Counter()
                        for ch in similar_children:
                            for d in ch.find_all(recursive=False):
                                for cls in _class_tokens(d):
                                    if _is_stable_css_token(cls):
                                        desc_class_counts[cls] += 1
                                        break  # Only consider first class-bearing child per item
                        if desc_class_counts:
                            top_cls, top_count = desc_class_counts.most_common(1)[0]
                            if top_count >= 3 and top_count >= max(
                                3, int(len(similar_children) * 0.6)
                            ):
                                shared_class = top_cls
                    if shared_class:
                        # Prefer class-only selector unless container has a stable id
                        if container.get("id"):
                            child_selector = f"{selector} > {most_common_tag}"
                        else:
                            child_selector = f".{shared_class}"

                    # Get sample text from first meaningful child
                    sample_child = (
                        meaningful_children[0]
                        if meaningful_children
                        else (similar_children[0] if similar_children else None)
                    )
                    sample_text = sample_child.get_text(strip=True)[:100] if sample_child else ""

                    # Calculate content score for ranking with hints
                    content_score = 0
                    hints: list[str] = []

                    if is_content_container(container):
                        content_score += 50
                        hints.append("content pattern")

                    # Bonus for semantic tags
                    if container.name in ['article', 'section', 'main']:
                        content_score += 30
                        hints.append(f"semantic <{container.name}>")
                    if most_common_tag in ['article', 'li', 'div']:
                        content_score += 20
                    if most_common_tag == 'tr':
                        content_score += 30
                        hints.append("table row")
                    if container.name in ['table', 'tbody']:
                        content_score += 20
                        hints.append("table container")

                    # Bonus for having links (articles usually link to detail pages)
                    effective_children = (
                        meaningful_children if meaningful_children else similar_children
                    )
                    avg_links = (
                        sum(1 for c in effective_children if c.find('a')) / len(effective_children)
                        if effective_children
                        else 0.0
                    )
                    if avg_links > 0.5:
                        content_score += 20
                        hints.append("has links")

                    # Bonus for having images (articles often have featured images)
                    avg_images = (
                        sum(1 for c in effective_children if c.find('img'))
                        / len(effective_children)
                        if effective_children
                        else 0.0
                    )
                    if avg_images > 0.3:
                        content_score += 15
                        hints.append("has images")

                    # Bonus for having headings (structured content)
                    avg_headings = (
                        sum(
                            1
                            for c in effective_children
                            if c.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        )
                        / len(effective_children)
                        if effective_children
                        else 0.0
                    )
                    if avg_headings > 0.3:
                        content_score += 15
                        hints.append("has headings")

                    # Bonus for item count (more items = more likely to be the main list)
                    if count >= 10:
                        content_score += 15
                        hints.append(f"{count} items")
                    elif count >= 5:
                        content_score += 10

                    containers.append(
                        {
                            "selector": selector,
                            "child_selector": child_selector,
                            "container_tag": container.name,
                            "child_tag": most_common_tag,
                            "item_count": count,
                            "sample_text": sample_text,
                            "container_class": _get_element_classes(container),
                            "container_id": container.get("id"),
                            "content_score": content_score,
                            "hints": hints,
                            "is_content": is_content_container(container),
                        }
                    )

    # Sort by content score first, then item count
    containers.sort(key=lambda x: (x["content_score"], x["item_count"]), reverse=True)

    # Return top 10
    return containers[:10]


def _extract_metadata(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract page metadata (title, description, etc.)."""
    metadata: dict[str, Any] = {}

    # Title
    title_tag = soup.find("title")
    metadata["title"] = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if not desc_tag:
        desc_tag = soup.find("meta", property="og:description")
    metadata["description"] = desc_tag.get("content", "") if desc_tag else ""

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    og_image = soup.find("meta", property="og:image")
    og_type = soup.find("meta", property="og:type")

    metadata["og"] = {
        "title": og_title.get("content") if og_title else None,
        "image": og_image.get("content") if og_image else None,
        "type": og_type.get("content") if og_type else None,
    }

    # Twitter Card
    twitter_card = soup.find("meta", attrs={"name": "twitter:card"})
    twitter_title = soup.find("meta", attrs={"name": "twitter:title"})

    metadata["twitter"] = {
        "card": twitter_card.get("content") if twitter_card else None,
        "title": twitter_title.get("content") if twitter_title else None,
    }

    # Language
    html_tag = soup.find("html")
    metadata["language"] = html_tag.get("lang") if html_tag else None

    # Canonical URL
    canonical = soup.find("link", rel="canonical")
    metadata["canonical"] = canonical.get("href") if canonical else None

    return metadata


def _calculate_statistics(soup: BeautifulSoup) -> dict[str, Any]:
    """Calculate page statistics."""
    stats: dict[str, Any] = {}

    # Count elements
    stats["total_elements"] = len(soup.find_all(True))
    stats["total_links"] = len(soup.find_all("a", href=True))
    stats["total_images"] = len(soup.find_all("img"))
    stats["total_forms"] = len(soup.find_all("form"))
    stats["total_tables"] = len(soup.find_all("table"))
    stats["total_lists"] = len(soup.find_all(["ul", "ol"]))

    # Count headings
    stats["headings"] = {f"h{i}": len(soup.find_all(f"h{i}")) for i in range(1, 7)}

    # Text length
    text = soup.get_text(strip=True)
    stats["text_length"] = len(text)
    stats["text_words"] = len(text.split())

    # Most common tags
    tag_counter = Counter(tag.name for tag in soup.find_all(True))
    stats["most_common_tags"] = tag_counter.most_common(10)

    # Most common classes
    class_counter: Counter[str] = Counter()
    for tag in soup.find_all(True):
        classes = _get_element_classes(tag)
        for cls in classes.split():
            if cls:
                class_counter[cls] += 1
    stats["most_common_classes"] = class_counter.most_common(10)

    return stats


def _generate_suggestions(
    soup: BeautifulSoup, containers: list[dict], frameworks: list[dict]
) -> dict[str, Any]:
    """Generate extraction suggestions based on analysis."""
    suggestions: dict[str, Any] = {}

    # Detect infinite scroll indicators
    suggestions["infinite_scroll"] = _detect_infinite_scroll(soup)

    # Best container guess
    if containers:
        suggestions["best_container"] = containers[0]
    else:
        suggestions["best_container"] = None

    suggestions["item_selector"] = None

    # Field suggestions based on first container
    if containers and containers[0]:
        best = containers[0]
        original_selector = best["child_selector"]
        try:
            items: list[Tag] = soup.select(original_selector)
        except Exception:
            items = []

        combined_items = _gather_similar_items(
            soup,
            containers,
            original_selector,
            limit=75,
        )

        if combined_items:
            items = combined_items

        generalized_selector = _generalize_item_selector(
            soup,
            items,
            original_selector,
            best.get("child_tag"),
            containers,
        )

        suggestions["item_selector"] = generalized_selector

        try:
            refreshed_items: list[Tag] = soup.select(generalized_selector)
        except Exception:
            refreshed_items = []

        if refreshed_items:
            items = refreshed_items
    else:
        items = []

    field_pool: dict[tuple[str, str, str | None], dict[str, Any]] = {}

    for item in items[:25]:  # limit for performance
        candidates = _suggest_fields(item)
        for candidate in candidates:
            name = str(candidate.get("name") or "")
            selector = str(candidate.get("selector") or "")
            attr_val = candidate.get("attribute")
            attribute = attr_val if isinstance(attr_val, str) else None
            key = (name, selector, attribute)

            if not key[0] or not key[1]:
                continue

            entry = field_pool.setdefault(
                key,
                {
                    "name": name,
                    "selector": selector,
                    "attribute": candidate.get("attribute"),
                    "sample": candidate.get("sample", ""),
                    "support": 0,
                    "count": 0,
                },
            )

            entry["support"] += 1
            entry["count"] += candidate.get("count", 0) or 0
            if not entry["sample"]:
                entry["sample"] = candidate.get("sample", "")

    if field_pool:
        ranked = sorted(
            field_pool.values(),
            key=lambda item: (item["support"], item["count"]),
            reverse=True,
        )

        selected: list[dict[str, Any]] = []
        seen_fields: set[str] = set()

        for candidate in ranked:
            name = candidate["name"]
            if name in seen_fields:
                continue
            selected.append(candidate)
            seen_fields.add(name)

        suggestions["field_candidates"] = selected
    else:
        suggestions["field_candidates"] = []

    # Pagination link suggestions
    suggestions["pagination_candidates"] = _detect_pagination_links(soup)

    # Framework-specific suggestions
    if frameworks:
        top_framework = frameworks[0]
        suggestions["framework_hint"] = {
            "name": top_framework["name"],
            "confidence": top_framework["confidence"],
            "recommendation": _get_framework_recommendation(top_framework["name"]),
        }
    else:
        suggestions["framework_hint"] = None

    return suggestions


def _generalize_item_selector(
    soup: BeautifulSoup,
    items: list[Tag],
    original_selector: str,
    child_tag: str | None,
    containers: list[dict[str, Any]],
) -> str:
    """Broaden suggested item selector when the original is overly specific."""

    if not original_selector:
        return original_selector

    id_prefix_candidates = _id_prefix_selector_candidates(containers, original_selector, child_tag)

    candidates: list[str] = []
    if original_selector:
        candidates.append(original_selector)
    candidates.extend(id_prefix_candidates)

    simplified = simplify_selector(original_selector)
    if simplified and simplified != original_selector:
        candidates.append(simplified)

    # Prefer stable class-based selectors shared across items (after structural variants)
    candidates.extend(_class_selector_candidates(items, child_tag))

    stripped = _strip_numeric_segments(original_selector)
    if stripped and stripped not in candidates:
        candidates.append(stripped)

    if child_tag and child_tag not in candidates:
        candidates.append(child_tag)

    # If we found an ID prefix candidate, also consider the bare prefix without explicit child tag
    if id_prefix_candidates:
        for candidate in id_prefix_candidates:
            if candidate.endswith(" > *"):
                continue
            prefix = candidate.split(" > ")[0]
            if prefix and f"{prefix} > *" not in candidates:
                candidates.append(f"{prefix} > *")

    seen: set[str] = set()
    for selector in candidates:
        if not selector or selector in seen:
            continue
        seen.add(selector)

        try:
            matches: list[Tag] = soup.select(selector)
        except Exception:
            continue

        if not matches:
            continue

        # Require selector to cover at least current items (or be the first workable option)
        if items and len(matches) < len(items):
            continue

        # Avoid selectors that explode across the whole document
        if items:
            max_allowed = max(500, len(items) * 8)
        else:
            max_allowed = 800
        if len(matches) > max_allowed:
            continue

        return selector

    return original_selector


def _gather_similar_items(
    soup: BeautifulSoup,
    containers: list[dict[str, Any]],
    base_selector: str,
    limit: int = 75,
) -> list[Tag]:
    """Collect items from containers that share structural selectors."""

    if not base_selector:
        return []

    collected: list[Tag] = []
    seen_selectors: set[str] = set()

    for container in containers:
        selector = container.get("child_selector")
        if not selector or selector in seen_selectors:
            continue

        if not _selectors_equivalent(base_selector, selector):
            continue

        seen_selectors.add(selector)

        try:
            matches: list[Tag] = soup.select(selector)
        except Exception:
            continue

        if not matches:
            continue

        collected.extend(matches)
        if len(collected) >= limit:
            break

    return collected[:limit]


def _class_selector_candidates(items: list[Tag], child_tag: str | None) -> list[str]:
    """Produce selector candidates using stable class names shared by items."""

    if not items:
        return []

    class_counts: Counter[str] = Counter()
    class_tag_hint: dict[str, str] = {}
    total_items = len(items)

    for item in items:
        own_classes = {cls for cls in _class_tokens(item) if _is_stable_css_token(cls)}
        for cls in own_classes:
            class_counts[cls] += 1
            class_tag_hint.setdefault(cls, item.name or "")

        # Look at direct children to find a more semantic descendant (e.g., article, tr)
        for child in item.find_all(recursive=False):
            child_classes = {cls for cls in _class_tokens(child) if _is_stable_css_token(cls)}
            for cls in child_classes:
                class_counts[cls] += 1
                # Prefer more semantic tags when available
                tag = child.name or ""
                if cls not in class_tag_hint or tag in {"article", "tr", "li", "div"}:
                    class_tag_hint[cls] = tag

    if not class_counts:
        return []

    threshold = 1 if total_items == 1 else max(2, total_items // 2)

    # Sort by frequency desc, length asc to prefer concise names
    ordered = sorted(
        (cls for cls, count in class_counts.items() if count >= threshold),
        key=lambda name: (-class_counts[name], len(name)),
    )

    candidates: list[str] = []
    for cls in ordered:
        tag_for_cls = class_tag_hint.get(cls) or child_tag
        if tag_for_cls:
            candidates.append(f"{tag_for_cls}.{cls}")
        candidates.append(f".{cls}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)

    return unique


def _id_prefix_selector_candidates(
    containers: list[dict[str, Any]],
    reference_selector: str,
    child_tag: str | None,
) -> list[str]:
    """Generate selectors using shared ID prefixes across containers."""

    reference_id = _extract_id_token(reference_selector)
    if not reference_id:
        return []

    related_ids = []
    for container in containers:
        selector = container.get("child_selector") or ""
        container_id = _extract_id_token(selector)
        if not container_id:
            continue
        if _shared_id_prefix(reference_id, container_id, minimum=4):
            related_ids.append(container_id)

    if len(related_ids) <= 1:
        return []

    prefix = _longest_common_prefix(related_ids)
    if not prefix or len(prefix) < 4:
        return []

    child = child_tag or _extract_child_tag(reference_selector) or "*"
    selector = f'[id^="{prefix}"] > {child}'
    return [selector]


def _strip_numeric_segments(selector: str) -> str:
    """Remove obviously year-based IDs/classes and nth-of-type markers."""

    if not selector:
        return selector

    cleaned = re.sub(r":nth-of-type\(\d+\)", "", selector)
    cleaned = re.sub(r"#[^\s>]*?(?:19|20)\d{2}[^\s>]*", "", cleaned)
    cleaned = re.sub(r"\.[^\s>]*?(?:19|20)\d{2}[^\s>]*", "", cleaned)
    cleaned = re.sub(r"\s*\>\s*", " > ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^(>\s*)+", "", cleaned).strip()

    return cleaned or selector


def _is_stable_css_token(value: str) -> bool:
    """Heuristic check to filter out dynamic or numeric-heavy class tokens."""

    if not value or len(value) < 3:
        return False

    lowered = value.lower()
    if lowered.startswith(("css-", "sc-", "jsx-", "emotion-", "_", "slick-")):
        return False

    if re.search(r"\d{4,}", value):
        return False

    if re.search(r"\d{3,}$", value):
        return False

    return True


def _selectors_equivalent(a: str | None, b: str | None) -> bool:
    """Check if two selectors are structurally equivalent after normalization."""

    if not a or not b:
        return False

    if _normalize_selector(a) == _normalize_selector(b):
        return True

    id_a = _extract_id_token(a)
    id_b = _extract_id_token(b)
    if id_a and id_b and _shared_id_prefix(id_a, id_b, minimum=4):
        child_a = _extract_child_tag(a)
        child_b = _extract_child_tag(b)
        if not child_a or not child_b or child_a == child_b:
            return True

    return False


def _normalize_selector(selector: str) -> str:
    """Normalize selector by simplifying and stripping numeric segments."""

    simplified = simplify_selector(selector) if selector else selector
    normalized = _strip_numeric_segments(simplified)
    return normalized or selector


def _extract_id_token(selector: str | None) -> str | None:
    if not selector:
        return None

    match = re.search(r"#([A-Za-z_][\w-]*)", selector)
    if match:
        return match.group(1).lower()
    return None


def _extract_child_tag(selector: str | None) -> str | None:
    if not selector:
        return None

    parts = [part.strip() for part in selector.split(">") if part.strip()]
    if not parts:
        return None

    last = parts[-1]
    if last.startswith("#") or last.startswith(".") or last.startswith("["):
        return None

    tag_match = re.match(r"^[a-zA-Z][a-zA-Z0-9-]*", last)
    if tag_match:
        return tag_match.group(0)
    return None


def _shared_id_prefix(a: str, b: str, minimum: int = 4) -> bool:
    prefix = _longest_common_prefix([a, b])
    return bool(prefix) and len(prefix) >= minimum


def _longest_common_prefix(values: list[str]) -> str:
    if not values:
        return ""

    prefix = values[0]
    for value in values[1:]:
        while not value.startswith(prefix) and prefix:
            prefix = prefix[:-1]
        if not prefix:
            break

    return prefix


def _detect_infinite_scroll(soup: BeautifulSoup) -> dict[str, Any]:
    """
    Detect if page uses infinite scroll instead of traditional pagination.

    Returns:
        Dictionary with detection results and indicators
    """
    indicators = {
        "detected": False,
        "confidence": 0.0,
        "signals": [],
    }

    score = 0
    signals = []

    # Check for common infinite scroll libraries/patterns
    html_str = str(soup)

    # JavaScript libraries for infinite scroll
    if "infinite-scroll" in html_str.lower():
        score += 30
        signals.append("infinite-scroll library detected")

    if "waypoint" in html_str.lower():
        score += 25
        signals.append("Waypoints.js (scroll detection library)")

    if "intersection observer" in html_str.lower() or "intersectionobserver" in html_str.lower():
        score += 30
        signals.append("IntersectionObserver API (modern infinite scroll)")

    # React/Vue infinite scroll components
    if any(lib in html_str for lib in ["react-infinite", "vue-infinite", "InfiniteScroll"]):
        score += 35
        signals.append("React/Vue infinite scroll component")

    # Check for absence of traditional pagination
    has_pagination = bool(
        soup.select(
            "a.next, a[rel='next'], .pagination a, a.page-link, nav[aria-label*='pagination' i]"
        )
    )

    if not has_pagination:
        score += 20
        signals.append("No traditional pagination links found")

    # Check for loading indicators (common in infinite scroll)
    loading_indicators = soup.select(
        ".loading, .spinner, .loader, [class*='load-more'], [id*='load-more']"
    )
    if loading_indicators:
        score += 15
        first_classes = loading_indicators[0].get("class")
        class_name = first_classes[0] if isinstance(first_classes, list) and first_classes else ""
        signals.append(f"Loading indicator found: {class_name}")

    # Check for scroll event listeners in scripts
    scripts = soup.find_all("script")
    for script in scripts:
        script_text = script.string or ""
        if any(pattern in script_text.lower() for pattern in ["scroll", "onscroll", "scrolltop"]):
            score += 10
            signals.append("Scroll event handlers in JavaScript")
            break

    # Data attributes suggesting dynamic loading
    if soup.select("[data-page], [data-offset], [data-cursor]"):
        score += 20
        signals.append("Pagination data attributes (likely API-driven)")

    # Calculate confidence
    confidence = min(score / 100.0, 1.0)

    indicators["detected"] = confidence > 0.3
    indicators["confidence"] = confidence
    indicators["signals"] = signals

    return indicators


def _detect_pagination_links(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Detect likely pagination "next" links on the page."""

    candidates: list[dict[str, Any]] = []
    seen_selectors: set[str] = set()

    anchors = soup.find_all("a", href=True)
    for anchor in anchors[:200]:  # limit to prevent runaway processing
        text = anchor.get_text(" ", strip=True)
        rel_raw = anchor.get("rel")
        rel_values = (
            " ".join(rel_raw)
            if isinstance(rel_raw, list)
            else (rel_raw if isinstance(rel_raw, str) else "")
        ).lower()
        aria_label = _attr_str(anchor, "aria-label").lower()
        data_testid = _attr_str(anchor, "data-testid").lower()
        classes = " ".join(_class_tokens(anchor)).lower()

        score = 0
        hints: list[str] = []

        if "next" in rel_values:
            score += 60
            hints.append("rel=next")
        if any(keyword in aria_label for keyword in ["next", "more", "older"]):
            score += 25
            hints.append("aria label")
        if any(keyword in data_testid for keyword in ["next", "pagination"]):
            score += 20
            hints.append("data-testid")
        if any(keyword in classes for keyword in ["next", "more", "older", "pagination"]):
            score += 20
            hints.append("class match")

        # Textual matches
        if re.search(r"\b(next|older|more|weiter|nächste|suivant)\b", text, re.I):
            score += 40
            hints.append("link text")
        if re.search(r"[»\u203A→⟩⟫]", text):
            score += 15
            hints.append("arrow symbol")

        if score < 40:
            continue

        selector = build_robust_selector(anchor)
        if not selector or selector in seen_selectors:
            continue

        seen_selectors.add(selector)
        candidates.append(
            {
                "selector": selector,
                "href": anchor.get("href"),
                "text": text[:80],
                "score": score,
                "hints": hints,
            }
        )

    # Deduplicate by href for cases where multiple selectors hit same target
    unique_candidates: dict[tuple[str, str], dict[str, Any]] = {}
    for candidate in candidates:
        href = candidate.get("href") or ""
        key = (candidate["selector"], href)
        existing = unique_candidates.get(key)
        if not existing or candidate["score"] > existing["score"]:
            unique_candidates[key] = candidate

    ranked = sorted(unique_candidates.values(), key=lambda c: c["score"], reverse=True)
    return ranked[:6]


def _suggest_fields(item: Tag) -> list[dict[str, Any]]:
    """Suggest field selectors within an item."""
    fields = []
    seen_selectors = set()  # Avoid duplicates

    # Enhanced field patterns with more comprehensive selectors
    patterns = [
        (
            "title",
            [
                "h1",
                "h2",
                "h3",
                "h4",
                ".title",
                ".headline",
                ".heading",
                ".name",
                ".card-title",
                "a.title",
                "a.headline",
                "strong span",
                "a strong span",
                ".archive strong span",
            ],
        ),
        (
            "link",
            [
                "a[href]",
                "h1 a",
                "h2 a",
                "h3 a",  # Links in headings
                ".title a",
                ".headline a",
            ],
        ),
        (
            "image",
            ["img[src]", "picture img", ".thumbnail img", ".featured-image img", ".card-img"],
        ),
        (
            "description",
            [
                "p",
                ".description",
                ".summary",
                ".excerpt",
                ".lead",
                ".snippet",
                ".card-text",
                ".body",
                ".content",
            ],
        ),
        (
            "date",
            [
                "time",
                "time[datetime]",
                ".date",
                ".published",
                ".timestamp",
                ".pubdate",
                ".post-date",
                ".article-date",
            ],
        ),
        (
            "author",
            [".author", ".byline", ".by", ".username", ".writer", "address", ".author-name"],
        ),
        ("price", [".price", ".cost", ".amount", ".value", ".sale-price", ".current-price"]),
        ("category", [".category", ".tag", ".label", ".section", ".topic", ".post-category"]),
    ]

    # Try each field pattern
    for field_name, selectors in patterns:
        for selector in selectors:
            try:
                elements = item.select(selector)
                if elements:
                    elem = elements[0]

                    # Skip if we've already found this selector
                    if selector in seen_selectors:
                        continue

                    # Get sample text or attribute
                    sample: str = ""
                    attribute: str | None = None

                    if field_name == "link":
                        sample = _attr_str(elem, "href")
                        attribute = "href"
                    elif field_name == "image":
                        sample = _attr_str(elem, "src")
                        attribute = "src"
                    elif field_name == "date" and _attr_str(elem, "datetime"):
                        sample = _attr_str(elem, "datetime")
                        attribute = "datetime"
                    else:
                        sample = elem.get_text(strip=True)

                    # Skip if sample is empty or too short
                    if not sample or len(sample.strip()) < 2:
                        continue

                    # Truncate sample
                    sample = sample[:50]

                    fields.append(
                        {
                            "name": field_name,
                            "selector": selector,
                            "sample": sample,
                            "count": len(elements),
                            "attribute": attribute,
                        }
                    )

                    seen_selectors.add(selector)
                    break  # Only one match per field type
            except Exception:
                continue

    # Also try to find any links not yet captured
    if not any(f["name"] == "link" for f in fields):
        links = item.find_all("a", href=True, limit=3)
        for idx, link in enumerate(links):
            href = _attr_str(link, "href")
            if href and not href.startswith("#"):
                selector = "a" if idx == 0 else f"a:nth-of-type({idx + 1})"
                fields.append(
                    {
                        "name": f"link_{idx + 1}" if idx > 0 else "link",
                        "selector": selector,
                        "sample": href[:50],
                        "count": 1,
                        "attribute": "href",
                    }
                )
                break

    return fields


def _get_framework_recommendation(framework_name: str) -> str:
    """Get extraction recommendation based on framework."""
    recommendations = {
        "schema_org": "Use structured data extractors - JSON-LD is already available",
        "opengraph": "Extract Open Graph meta tags for rich previews",
        "twitter_cards": "Extract Twitter Card meta tags for social sharing data",
        "bootstrap": "Look for .card, .list-group-item, .row patterns",
        "tailwind": "Classes are utility-based, rely on semantic HTML structure",
        "react": "May be client-side rendered - check for data-reactid or __NEXT_DATA__",
        "vue": "May use v- directives, look for Vue-specific patterns",
        "nextjs": "Check __NEXT_DATA__ script tag for pre-rendered data",
        "wordpress": "Look for .post, .entry, WP-specific classes",
        "drupal": "Check for .node, .field patterns",
        "shopify": "Product data often in JSON scripts or meta tags",
        "woocommerce": "Products use .product, .woocommerce patterns",
    }
    return recommendations.get(framework_name, "No specific recommendation")
