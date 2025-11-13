"""Core analysis engine for Probe tool."""

from collections import Counter
from typing import Any

from bs4 import BeautifulSoup, Tag

from foundry.framework_profiles import _get_element_classes, detect_all_frameworks
from foundry.lib.selectors import build_robust_selector


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
        
        frameworks.append({
            "name": framework_name,
            "confidence": confidence,
            "version": version,
            "score": score,
        })
    
    # Sort by confidence (already sorted by detect_all_frameworks)
    frameworks.sort(key=lambda x: x["confidence"], reverse=True)
    
    return frameworks


def _find_containers(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Find container elements with repeated children (likely item lists)."""
    containers = []
    
    # Blacklist of common boilerplate selectors/classes that should be deprioritized
    BOILERPLATE_PATTERNS = [
        'header', 'footer', 'nav', 'navigation', 'menu', 'sidebar', 
        'breadcrumb', 'cookie', 'banner', 'ad', 'advertisement',
        'social', 'share', 'toolbar', 'utility', 'meta', 'promo',
        'related', 'widget', 'plugin', 'tracking'
    ]
    
    # Prioritize content containers
    CONTENT_PATTERNS = [
        'article', 'post', 'story', 'item', 'card', 'entry', 'product',
        'result', 'listing', 'content', 'main', 'feed', 'list'
    ]
    
    def is_boilerplate(element: Tag) -> bool:
        """Check if element is likely boilerplate."""
        classes = _get_element_classes(element).lower()
        elem_id = (element.get("id") or "").lower()
        combined = f"{classes} {elem_id}"
        
        return any(pattern in combined for pattern in BOILERPLATE_PATTERNS)
    
    def is_content_container(element: Tag) -> bool:
        """Check if element is likely a content container."""
        classes = _get_element_classes(element).lower()
        elem_id = (element.get("id") or "").lower()
        combined = f"{classes} {elem_id}"
        
        return any(pattern in combined for pattern in CONTENT_PATTERNS)
    
    def has_meaningful_content(element: Tag) -> bool:
        """Check if child has substantial text content (not just links/buttons)."""
        text = element.get_text(strip=True)
        
        # Check for presence of headings or paragraphs (strong signal)
        if element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            return True
        
        # Check for substantial text (more than just a few words)
        if len(text) < 15:
            return False
        
        # Check text to link ratio
        links = element.find_all('a')
        link_text = sum(len(a.get_text(strip=True)) for a in links)
        if link_text > 0 and len(text) / link_text > 2:
            return True
        
        return len(text) > 50
    
    for container_tag in ["div", "section", "article", "ul", "ol", "main", "aside"]:
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
                    similar_children = [c for c in children if hasattr(c, 'name') and c.name == most_common_tag]
                    
                    # Filter out if children don't have meaningful content
                    meaningful_children = [c for c in similar_children if has_meaningful_content(c)]
                    if len(meaningful_children) < 3:
                        continue
                    
                    selector = build_robust_selector(container)
                    child_selector = f"{selector} > {most_common_tag}"
                    
                    # Get sample text from first meaningful child
                    sample_child = meaningful_children[0] if meaningful_children else None
                    sample_text = sample_child.get_text(strip=True)[:100] if sample_child else ""
                    
                    # Calculate content score for ranking
                    content_score = 0
                    if is_content_container(container):
                        content_score += 50
                    
                    # Bonus for semantic tags
                    if container.name in ['article', 'section', 'main']:
                        content_score += 30
                    if most_common_tag in ['article', 'li', 'div']:
                        content_score += 20
                    
                    # Bonus for having links (articles usually link to detail pages)
                    avg_links = sum(1 for c in meaningful_children if c.find('a')) / len(meaningful_children)
                    if avg_links > 0.5:
                        content_score += 20
                    
                    # Bonus for having images (articles often have featured images)
                    avg_images = sum(1 for c in meaningful_children if c.find('img')) / len(meaningful_children)
                    if avg_images > 0.3:
                        content_score += 15
                    
                    containers.append({
                        "selector": selector,
                        "child_selector": child_selector,
                        "container_tag": container.name,
                        "child_tag": most_common_tag,
                        "item_count": count,
                        "sample_text": sample_text,
                        "container_class": _get_element_classes(container),
                        "container_id": container.get("id"),
                        "content_score": content_score,
                        "is_content": is_content_container(container),
                    })
    
    # Sort by content score first, then item count
    containers.sort(key=lambda x: (x["content_score"], x["item_count"]), reverse=True)
    
    # Return top 10
    return containers[:10]


def _extract_metadata(soup: BeautifulSoup) -> dict[str, Any]:
    """Extract page metadata (title, description, etc.)."""
    metadata = {}
    
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
    stats = {}
    
    # Count elements
    stats["total_elements"] = len(soup.find_all(True))
    stats["total_links"] = len(soup.find_all("a", href=True))
    stats["total_images"] = len(soup.find_all("img"))
    stats["total_forms"] = len(soup.find_all("form"))
    stats["total_tables"] = len(soup.find_all("table"))
    stats["total_lists"] = len(soup.find_all(["ul", "ol"]))
    
    # Count headings
    stats["headings"] = {
        f"h{i}": len(soup.find_all(f"h{i}"))
        for i in range(1, 7)
    }
    
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


def _generate_suggestions(soup: BeautifulSoup, containers: list[dict], frameworks: list[dict]) -> dict[str, Any]:
    """Generate extraction suggestions based on analysis."""
    suggestions = {}
    
    # Detect infinite scroll indicators
    suggestions["infinite_scroll"] = _detect_infinite_scroll(soup)
    
    # Best container guess
    if containers:
        suggestions["best_container"] = containers[0]
        suggestions["item_selector"] = containers[0]["child_selector"]
    else:
        suggestions["best_container"] = None
        suggestions["item_selector"] = None
    
    # Field suggestions based on first container
    if containers and containers[0]:
        best = containers[0]
        # Parse the selector to get actual elements
        try:
            items = soup.select(best["child_selector"])
            if items:
                first_item = items[0]
                suggestions["field_candidates"] = _suggest_fields(first_item)
            else:
                suggestions["field_candidates"] = []
        except Exception:
            suggestions["field_candidates"] = []
    else:
        suggestions["field_candidates"] = []
    
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
        soup.select("a.next, a[rel='next'], .pagination a, a.page-link, nav[aria-label*='pagination' i]")
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
        signals.append(f"Loading indicator found: {loading_indicators[0].get('class', [''])[0]}")
    
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


def _suggest_fields(item: Tag) -> list[dict[str, str]]:
    """Suggest field selectors within an item."""
    fields = []
    seen_selectors = set()  # Avoid duplicates
    
    # Enhanced field patterns with more comprehensive selectors
    patterns = [
        ("title", [
            "h1", "h2", "h3", "h4", 
            ".title", ".headline", ".heading", ".name", ".card-title",
            "a.title", "a.headline"
        ]),
        ("link", [
            "a[href]", 
            "h1 a", "h2 a", "h3 a",  # Links in headings
            ".title a", ".headline a"
        ]),
        ("image", [
            "img[src]", 
            "picture img", 
            ".thumbnail img", ".featured-image img", ".card-img"
        ]),
        ("description", [
            "p", 
            ".description", ".summary", ".excerpt", ".lead", ".snippet",
            ".card-text", ".body", ".content"
        ]),
        ("date", [
            "time", "time[datetime]",
            ".date", ".published", ".timestamp", ".pubdate",
            ".post-date", ".article-date"
        ]),
        ("author", [
            ".author", ".byline", ".by", ".username", ".writer",
            "address", ".author-name"
        ]),
        ("price", [
            ".price", ".cost", ".amount", ".value",
            ".sale-price", ".current-price"
        ]),
        ("category", [
            ".category", ".tag", ".label", ".section", ".topic",
            ".post-category"
        ]),
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
                    sample = ""
                    attribute = None
                    
                    if field_name == "link":
                        sample = elem.get("href", "")
                        attribute = "href"
                    elif field_name == "image":
                        sample = elem.get("src", "")
                        attribute = "src"
                    elif field_name == "date" and elem.get("datetime"):
                        sample = elem.get("datetime", "")
                        attribute = "datetime"
                    else:
                        sample = elem.get_text(strip=True)
                    
                    # Skip if sample is empty or too short
                    if not sample or len(sample.strip()) < 2:
                        continue
                    
                    # Truncate sample
                    sample = sample[:50]
                    
                    fields.append({
                        "name": field_name,
                        "selector": selector,
                        "sample": sample,
                        "count": len(elements),
                        "attribute": attribute,
                    })
                    
                    seen_selectors.add(selector)
                    break  # Only one match per field type
            except Exception:
                continue
    
    # Also try to find any links not yet captured
    if not any(f["name"] == "link" for f in fields):
        links = item.find_all("a", href=True, limit=3)
        for idx, link in enumerate(links):
            href = link.get("href", "")
            if href and not href.startswith("#"):
                selector = "a" if idx == 0 else f"a:nth-of-type({idx + 1})"
                fields.append({
                    "name": f"link_{idx + 1}" if idx > 0 else "link",
                    "selector": selector,
                    "sample": href[:50],
                    "count": 1,
                    "attribute": "href",
                })
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
