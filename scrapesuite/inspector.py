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
            
            # Extract sample data - try multiple strategies for better context
            link_elem = first.find("a", href=True)
            
            # Get sample text - prioritize meaningful content
            sample_title = ""
            
            # Try to find a good title/heading
            title_elem = first.find(["h1", "h2", "h3", "h4"])
            if title_elem and title_elem.get_text(strip=True):
                sample_title = title_elem.get_text(strip=True)[:80]
            
            # Try prominent link text
            if not sample_title and link_elem:
                link_text = link_elem.get_text(strip=True)
                if link_text and len(link_text) > 3:  # Ignore short links like ">"
                    sample_title = link_text[:80]
            
            # Try any substantial text content
            if not sample_title:
                all_text = first.get_text(strip=True)
                # Even short text is useful if that's all there is
                if all_text:
                    # For very short text (like "1."), show it directly
                    if len(all_text) <= 10:
                        sample_title = f"Text: '{all_text}'"
                    else:
                        sample_title = all_text[:80]
            
            # Build descriptive summary if no meaningful text found
            if not sample_title:
                parts = []
                
                # Describe element type
                parts.append(f"<{first.name}>")
                
                # Show what types of child elements exist
                child_tags = [child.name for child in first.find_all(recursive=False)]
                if child_tags:
                    unique_tags = sorted(set(child_tags))[:3]
                    parts.append(f"contains {', '.join(unique_tags)}")
                
                # Show if it has links
                link_count = len(first.find_all("a"))
                if link_count > 0:
                    parts.append(f"{link_count} link{'s' if link_count != 1 else ''}")
                
                # Show if it has specific attributes that might identify it
                if first.get("id"):
                    parts.append(f"id='{first.get('id')}'")
                
                sample_title = " | ".join(parts) if len(parts) > 1 else parts[0] if parts else "container"
            
            candidates.append({
                "selector": f".{cls}",
                "count": count,
                "sample_title": sample_title,
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
            # Add only if not already covered by class-only selector
            selector_class = pattern.split(".")[-1]
            if not any(c["selector"] == f".{selector_class}" for c in candidates):
                candidates.append({
                    "selector": pattern.replace(".", "."),
                    "count": count,
                    "sample_title": f"<{pattern.split('.')[0]}> element",
                    "confidence": "medium",
                })
    
    # Strategy 3: Semantic HTML tags (article, li, tr)
    semantic_tags = ["article", "li", "tr"]
    for tag_name in semantic_tags:
        elements = soup.find_all(tag_name)
        count = len(elements)
        
        if count >= min_items:
            # Check if not already covered by class selector
            selector = tag_name
            if not any(selector in c["selector"] for c in candidates):
                first = elements[0]
                
                # Extract sample title using same logic as above
                sample_title = ""
                title_elem = first.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                if title_elem:
                    sample_title = title_elem.get_text(strip=True)[:80]
                
                if not sample_title:
                    link_elem = first.find("a", href=True)
                    if link_elem:
                        link_text = link_elem.get_text(strip=True)
                        if link_text and len(link_text) > 3:
                            sample_title = link_text[:80]
                
                if not sample_title:
                    all_text = first.get_text(strip=True)
                    if all_text:
                        sample_title = all_text[:80] if len(all_text) > 10 else f"Text: '{all_text}'"
                
                if not sample_title:
                    sample_title = f"<{tag_name}> element"
                
                candidates.append({
                    "selector": selector,
                    "count": count,
                    "sample_title": sample_title,
                    "sample_url": first.find("a", href=True).get("href") if first.find("a", href=True) else "",
                    "confidence": "medium",
                })
    
    # Strategy 4: Parent containers with repeated children
    # Look for containers (ul, ol, tbody, div) that have many similar children
    container_tags = ["ul", "ol", "tbody", "div"]
    for container_tag in container_tags:
        containers = soup.find_all(container_tag)
        for container in containers:
            # Get direct children only (filter out None/text nodes)
            children = [child for child in container.children if hasattr(child, 'name') and child.name]
            if not children:
                continue
            
            # Count children by tag name
            child_tag_counts = Counter(child.name for child in children)
            
            for child_tag, child_count in child_tag_counts.items():
                if child_count >= min_items and child_tag:  # Ensure child_tag is not None
                    # Build selector: "ul > li" or "tbody > tr"
                    selector = f"{container_tag} > {child_tag}"
                    
                    # Check if similar selector already exists
                    if any(child_tag in c["selector"] for c in candidates):
                        continue
                    
                    # Get sample from first child
                    first_child = next(c for c in children if c.name == child_tag)
                    sample_title = ""
                    
                    heading = first_child.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                    if heading:
                        sample_title = heading.get_text(strip=True)[:80]
                    
                    if not sample_title:
                        link = first_child.find("a", href=True)
                        if link:
                            link_text = link.get_text(strip=True)
                            if link_text and len(link_text) > 3:
                                sample_title = link_text[:80]
                    
                    if not sample_title:
                        sample_title = first_child.get_text(strip=True)[:80] or f"<{child_tag}> element"
                    
                    candidates.append({
                        "selector": selector,
                        "count": child_count,
                        "sample_title": sample_title,
                        "sample_url": first_child.find("a", href=True).get("href") if first_child.find("a", href=True) else "",
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
        # Look for headings first (most semantic)
        for tag in ["h1", "h2", "h3", "h4"]:
            elem = item_element.find(tag)
            if elem and elem.get_text(strip=True):
                classes = elem.get("class", [])
                if classes:
                    return f"{tag}.{classes[0]}"
                return tag
        
        # Score all links and pick the best candidate
        link_candidates = []
        for a in item_element.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a.get("href", "")
            
            # Skip obvious non-content links
            if not text or href.startswith("#") or href.startswith("javascript:"):
                continue
            
            score = 0
            
            # Prefer longer text (likely article titles, not "Read more")
            score += min(len(text), 100)  # Cap at 100 to avoid huge bias
            
            # Penalize very short text unless it's emoji/unicode
            if len(text) <= 3 and text.isascii():
                score -= 50
            
            # Boost for semantic attributes
            if a.get("rel") and "bookmark" in str(a.get("rel")):
                score += 20
            if a.get("itemprop") and "name" in str(a.get("itemprop")):
                score += 20
            
            # Penalize common navigation/UI patterns
            classes = " ".join(a.get("class", [])).lower()
            if any(word in classes for word in ["vote", "upvote", "reply", "share", "flag", "hide"]):
                score -= 30
            if any(word in text.lower() for word in ["vote", "reply", "share", "hide", "save", "report"]):
                score -= 30
            
            link_candidates.append((score, a))
        
        # Pick highest scoring link
        if link_candidates:
            link_candidates.sort(reverse=True, key=lambda x: x[0])
            best_link = link_candidates[0][1]
            
            classes = best_link.get("class", [])
            if classes:
                return f"a.{classes[0]}"
            # Use parent context for specificity
            parent = best_link.parent
            if parent and parent.get("class"):
                parent_class = parent.get("class")[0]
                return f".{parent_class} a"
            return "a"
    
    elif field_type == "url":
        # Reuse title logic but append ::attr(href)
        title_selector = generate_field_selector(item_element, "title")
        if title_selector:
            return f"{title_selector}::attr(href)"
    
    elif field_type == "date":
        # Look for time element or common date patterns
        time_elem = item_element.find("time")
        if time_elem:
            classes = time_elem.get("class", [])
            if classes:
                return f"time.{classes[0]}"
            return "time"
        
        # Try semantic attributes
        datetime_elem = item_element.find(attrs={"datetime": True})
        if datetime_elem:
            classes = datetime_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
        
        # Score elements by date-related signals (works across languages)
        candidates = []
        for elem in item_element.find_all(["span", "div", "p", "small"]):
            score = 0
            text = elem.get_text(strip=True)
            classes = " ".join(elem.get("class", [])).lower()
            
            # Keyword matching (English and common patterns)
            if any(kw in classes for kw in ["date", "time", "timestamp", "posted", "published", "ago", "when"]):
                score += 30
            
            # Text pattern matching (language-agnostic)
            import re
            # ISO dates, timestamps, "X ago" patterns
            if re.search(r'\d{4}-\d{2}-\d{2}', text):  # ISO date
                score += 20
            if re.search(r'\d+\s*(second|minute|hour|day|week|month|year|ago|h|m|d)', text, re.I):
                score += 15
            if re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', text):  # Date formats
                score += 15
            
            if score > 0:
                candidates.append((score, elem))
        
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            best_elem = candidates[0][1]
            classes = best_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
            return best_elem.name
    
    elif field_type == "author":
        # Try semantic attributes first
        author_elem = item_element.find(attrs={"itemprop": "author"})
        if not author_elem:
            author_elem = item_element.find(attrs={"rel": "author"})
        if author_elem:
            classes = author_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
            return author_elem.name
        
        # Score elements by author-related signals
        candidates = []
        for elem in item_element.find_all(["span", "a", "div", "p", "small"]):
            score = 0
            classes = " ".join(elem.get("class", [])).lower()
            text = elem.get_text(strip=True)
            
            # Keyword matching (expand for multilingual)
            if any(kw in classes for kw in ["author", "user", "username", "by", "posted-by", "submitter", "creator"]):
                score += 30
            
            # Text patterns that suggest authorship
            if text.startswith("by ") or text.startswith("@"):
                score += 15
            
            # Penalize very long text (unlikely to be just a username)
            if len(text) > 50:
                score -= 10
            
            if score > 0:
                candidates.append((score, elem))
        
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            best_elem = candidates[0][1]
            classes = best_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
            return best_elem.name
    
    elif field_type == "score":
        # Score elements by voting/scoring signals
        candidates = []
        for elem in item_element.find_all(["span", "div", "p", "small"]):
            score = 0
            text = elem.get_text(strip=True)
            classes = " ".join(elem.get("class", [])).lower()
            
            # Keyword matching
            if any(kw in classes for kw in ["score", "points", "votes", "upvotes", "rating", "karma", "likes"]):
                score += 30
            
            # Text patterns (numbers followed by "points", etc.)
            import re
            if re.search(r'\d+\s*(point|vote|upvote|like|star)', text, re.I):
                score += 20
            # Just a number (might be score)
            if re.match(r'^\d+$', text):
                score += 5
            
            if score > 0:
                candidates.append((score, elem))
        
        if candidates:
            candidates.sort(reverse=True, key=lambda x: x[0])
            best_elem = candidates[0][1]
            classes = best_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
            return best_elem.name
    
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
