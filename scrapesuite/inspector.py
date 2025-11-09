"""HTML inspection utilities for building selectors."""

from collections import Counter
from typing import Any

from bs4 import BeautifulSoup, Tag


def inspect_html(html: str) -> dict[str, Any]:
    """
    Analyze HTML structure to find common patterns.
    
    Returns dict with:
    - repeated_elements: Elements that appear multiple times (likely items)
    - common_containers: Container elements (ul, ol, table, div with multiple children)
    - links: Anchor tags with hrefs
    - metadata: Page title, description, etc.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Find repeated element patterns
    tag_counter = Counter()
    class_counter = Counter()
    
    for tag in soup.find_all(True):  # All tags
        # Count tags
        tag_counter[tag.name] += 1
        
        # Count classes
        classes = tag.get("class", [])
        for cls in classes:
            class_counter[cls] += 1
    
    # Find container candidates (divs/sections with repeated children)
    containers = []
    for container_tag in ["div", "section", "article", "ul", "ol", "table"]:
        for container in soup.find_all(container_tag):
            children = list(container.find_all(recursive=False))
            if len(children) >= 3:  # At least 3 repeated items
                # Check if children have same tag/class
                child_tags = [c.name for c in children]
                if len(set(child_tags)) == 1:  # All same tag
                    containers.append({
                        "tag": container.name,
                        "class": " ".join(container.get("class", [])),
                        "id": container.get("id"),
                        "child_count": len(children),
                        "child_tag": child_tags[0],
                        "sample": str(children[0])[:200],
                    })
    
    # Find repeated class patterns (likely items)
    repeated_classes = []
    for cls, count in class_counter.most_common(20):
        if count >= 3 and cls:  # At least 3 occurrences
            elements = soup.find_all(class_=cls)
            sample = elements[0] if elements else None
            repeated_classes.append({
                "class": cls,
                "count": count,
                "tag": sample.name if sample else None,
                "sample_text": sample.get_text(strip=True)[:100] if sample else "",
            })
    
    # Get all links
    links = []
    for a in soup.find_all("a", href=True):
        links.append({
            "href": a.get("href"),
            "text": a.get_text(strip=True),
            "class": " ".join(a.get("class", [])),
        })
    
    # Page metadata
    title = soup.find("title")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    
    return {
        "title": title.get_text(strip=True) if title else "",
        "description": meta_desc.get("content", "") if meta_desc else "",
        "total_links": len(links),
        "containers": sorted(containers, key=lambda x: x["child_count"], reverse=True)[:5],
        "repeated_classes": repeated_classes[:10],
        "sample_links": links[:10],
    }


def find_item_selector(html: str, min_items: int = 3) -> list[dict[str, Any]]:
    """
    Detect likely item selectors (repeated elements).
    
    Returns list of potential item containers with CSS selectors.
    """
    soup = BeautifulSoup(html, "html.parser")
    candidates = []
    
    # Strategy 1: Look for repeated classes
    class_counts = Counter()
    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        for cls in classes:
            class_counts[cls] += 1
    
    for cls, count in class_counts.items():
        if count >= min_items and cls:
            elements = soup.find_all(class_=cls)
            first = elements[0]
            
            # Extract sample data
            title_elem = first.find(["h1", "h2", "h3", "h4", "a"])
            link_elem = first.find("a", href=True)
            
            candidates.append({
                "selector": f".{cls}",
                "count": count,
                "sample_title": title_elem.get_text(strip=True)[:80] if title_elem else "",
                "sample_url": link_elem.get("href") if link_elem else "",
                "confidence": "high" if count >= 10 else "medium",
            })
    
    # Strategy 2: Look for repeated tag patterns
    tag_class_patterns = Counter()
    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        if classes:
            pattern = f"{tag.name}.{classes.split()[0]}"
            tag_class_patterns[pattern] += 1
    
    for pattern, count in tag_class_patterns.items():
        if count >= min_items:
            candidates.append({
                "selector": pattern.replace(".", "."),
                "count": count,
                "confidence": "medium",
            })
    
    # Sort by count and confidence
    return sorted(candidates, key=lambda x: x["count"], reverse=True)[:5]


def generate_field_selector(item_element: Tag, field_type: str) -> str | None:  # noqa: PLR0911, PLR0912
    """
    Generate CSS selector for common field types within an item.
    
    Args:
        item_element: BeautifulSoup Tag representing the item container
        field_type: One of 'title', 'url', 'date', 'author', 'score', 'image'
    
    Returns:
        CSS selector string or None if not found
    """
    if field_type == "title":
        # Look for headings or prominent links
        for tag in ["h1", "h2", "h3", "h4", "a"]:
            elem = item_element.find(tag)
            if elem:
                classes = elem.get("class", [])
                if classes:
                    return f"{tag}.{classes[0]}"
                return tag
    
    elif field_type == "url":
        # Find first anchor with href
        a = item_element.find("a", href=True)
        if a:
            classes = a.get("class", [])
            if classes:
                return f"a.{classes[0]}"
            return "a"
    
    elif field_type == "date":
        # Look for time element or common date classes
        time_elem = item_element.find("time")
        if time_elem:
            return "time"
        
        for keyword in ["date", "timestamp", "time", "posted", "published"]:
            elem = item_element.find(class_=lambda x, kw=keyword: x and kw in x.lower())
            if elem:
                return f".{elem.get('class')[0]}"
    
    elif field_type == "author":
        # Look for author/username classes
        for keyword in ["author", "user", "username", "by"]:
            elem = item_element.find(class_=lambda x, kw=keyword: x and kw in x.lower())
            if elem:
                return f".{elem.get('class')[0]}"
    
    elif field_type == "score":
        # Look for score/points/votes classes
        for keyword in ["score", "points", "votes", "upvotes", "rating"]:
            elem = item_element.find(class_=lambda x, kw=keyword: x and kw in x.lower())
            if elem:
                return f".{elem.get('class')[0]}"
    
    elif field_type == "image":
        # Find first img tag
        img = item_element.find("img")
        if img:
            classes = img.get("class", [])
            if classes:
                return f"img.{classes[0]}"
            return "img"
    
    return None


def preview_extraction(html: str, item_selector: str, field_selectors: dict[str, str]) -> list[dict]:
    """
    Preview what would be extracted with given selectors.
    
    Args:
        html: HTML content
        item_selector: CSS selector for item containers
        field_selectors: Dict mapping field names to CSS selectors
    
    Returns:
        List of extracted items (limited to first 3)
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(item_selector)
    
    previews = []
    for item in items[:3]:  # Limit to 3 for preview
        data = {}
        for field_name, selector in field_selectors.items():
            try:
                # Handle attribute extraction
                if "::attr(" in selector:
                    attr_name = selector.split("::attr(")[1].rstrip(")")
                    if selector.startswith("::attr"):
                        # Extract from item itself
                        data[field_name] = item.get(attr_name, "")
                    else:
                        # Extract from child
                        child_selector = selector.split("::attr")[0].strip()
                        elem = item.select_one(child_selector)
                        data[field_name] = elem.get(attr_name, "") if elem else ""
                else:
                    # Text extraction
                    elem = item.select_one(selector)
                    data[field_name] = elem.get_text(strip=True) if elem else ""
            except Exception:
                data[field_name] = "[extraction failed]"
        
        previews.append(data)
    
    return previews


def suggest_field_name(selector: str, sample_text: str) -> str:  # noqa: PLR0911
    """
    Suggest a field name based on selector and sample content.
    
    Examples:
        .title, "My Article" -> "title"
        .score, "123 points" -> "score"
        time, "2024-01-15" -> "date"
    """
    # Extract class name if present
    if "." in selector:
        class_name = selector.split(".")[1].split()[0]
        # Common mappings
        if any(word in class_name.lower() for word in ["title", "heading"]):
            return "title"
        if any(word in class_name.lower() for word in ["score", "points", "votes"]):
            return "score"
        if any(word in class_name.lower() for word in ["author", "user"]):
            return "author"
        if any(word in class_name.lower() for word in ["date", "time", "posted"]):
            return "date"
        if any(word in class_name.lower() for word in ["comment", "replies"]):
            return "comments"
        return class_name.lower().replace("-", "_")
    
    # Analyze sample text
    if sample_text:
        lower_text = sample_text.lower()
        if "points" in lower_text or "votes" in lower_text:
            return "score"
        if "@" in sample_text or "by " in lower_text:
            return "author"
        if any(char.isdigit() for char in sample_text) and len(sample_text) < 20:
            return "count"
    
    return "field"
