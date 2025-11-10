"""HTML inspection utilities for building selectors."""

from collections import Counter
from typing import Any

from bs4 import BeautifulSoup, Tag

from .selector_builder import build_robust_selector


def inspect_html(html: str) -> dict[str, Any]:
    """
    Analyze HTML structure to find common patterns.
    
    Returns dict with:
    - repeated_elements: Elements that appear multiple times (likely items)
    - common_containers: Container elements (ul, ol, table, div with multiple children)
    - links: Anchor tags with hrefs
    - metadata: Page title, description, etc.
    """
    if not html or not html.strip():
        return {
            "title": "",
            "description": "",
            "total_links": 0,
            "repeated_classes": [],
            "sample_links": [],
        }
    
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


def find_item_selector(html: str, min_items: int = 3) -> list[dict[str, Any]]:  # noqa: PLR0915
    """
    Detect likely item selectors (repeated elements).
    
    Returns list of potential item containers with CSS selectors.
    """
    if not html or not html.strip():
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Check if we got meaningful HTML (not just error page or empty)
    if not soup.find("body") and not soup.find("html"):
        # Might be a fragment, try to parse anyway
        pass
    
    candidates = []
    
    # Strategy 0: Find parent containers of repeated field groups
    # This is crucial for sites like FDA/Drupal where fields are siblings, not nested
    # Look for elements that contain multiple children with similar class patterns
    class_pattern_parents = Counter()
    parent_examples = {}  # Store first example of each parent
    
    for tag in soup.find_all(True):
        classes = tag.get("class", [])
        if not classes:
            continue
        
        # Look for class patterns like "views-field-*", "field-*", "item-*"
        for cls in classes:
            # Check if this class has a common prefix pattern
            if any(pattern in cls for pattern in ["views-field", "field-", "item-", "post-", "entry-", "article-"]):
                # Find parent
                parent = tag.parent
                if parent and parent.name not in ["body", "html", "head"]:
                    # Create a signature for the parent
                    parent_classes = " ".join(parent.get("class", []))
                    parent_sig = f"{parent.name}.{parent_classes.split()[0]}" if parent_classes else parent.name
                    class_pattern_parents[parent_sig] += 1
                    
                    # Store first example
                    if parent_sig not in parent_examples:
                        parent_examples[parent_sig] = parent
    
    # Add high-confidence parent containers
    # But only if they actually represent distinct items, not just field counts
    for parent_sig, field_count in class_pattern_parents.items():
        # field_count is the number of child fields with pattern prefixes
        # We want to find how many actual parent elements exist
        
        # Find actual elements matching this signature
        if "." in parent_sig:
            tag_name, class_name = parent_sig.split(".", 1)
            parent_elements = soup.find_all(tag_name, class_=class_name)
        else:
            parent_elements = soup.find_all(parent_sig)
        
        actual_count = len(parent_elements)
        
        # Only add if we have multiple instances AND multiple fields per instance
        # This filters out single containers with many fields vs many items with fields
        if actual_count >= min_items and field_count >= actual_count * 2:
            # Likely a good candidate: multiple items, each with multiple fields
            first = parent_elements[0]
            
            # Extract sample title from first element
            sample_title = ""
            title_elem = first.find(["h1", "h2", "h3", "h4"])
            if title_elem:
                sample_title = title_elem.get_text(strip=True)[:80]
            
            if not sample_title:
                link_elem = first.find("a", href=True)
                if link_elem:
                    sample_title = link_elem.get_text(strip=True)[:80]
            
            if not sample_title:
                sample_title = first.get_text(strip=True)[:80] or f"<{parent_sig}> container"
            
            # Extract multiple samples for clarity
            sample_texts = []
            num_samples = min(3, actual_count)
            for elem in parent_elements[:num_samples]:
                elem_text = ""
                heading = elem.find(["h1", "h2", "h3", "h4"])
                if heading:
                    elem_text = heading.get_text(strip=True)[:50]
                if not elem_text:
                    elem_link = elem.find("a", href=True)
                    if elem_link:
                        elem_text = elem_link.get_text(strip=True)[:50]
                if not elem_text:
                    elem_text = elem.get_text(strip=True)[:50]
                
                if elem_text:
                    sample_texts.append(elem_text)
            
            # Deduplicate and join
            unique_samples = list(dict.fromkeys(sample_texts))
            if len(unique_samples) > 1:
                sample_title = " | ".join(unique_samples)
            elif unique_samples:
                sample_title = unique_samples[0]
            
            selector = f".{parent_sig.split('.')[-1]}" if "." in parent_sig else parent_sig
            
            candidates.append({
                "selector": selector,
                "count": actual_count,
                "sample_title": sample_title,
                "sample_url": first.find("a", href=True).get("href", "") if first.find("a", href=True) else "",
                "confidence": "high",  # High confidence for field group parents
            })
    
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
            
            # NEW: Check if we should show multiple samples for clarity
            # If we have 2-5 items, show them all; if more, show first 3
            sample_texts = []
            num_samples = min(3, count)
            for elem in elements[:num_samples]:
                elem_text = ""
                # Try heading first
                heading = elem.find(["h1", "h2", "h3", "h4"])
                if heading:
                    elem_text = heading.get_text(strip=True)[:50]
                # Try link
                if not elem_text:
                    elem_link = elem.find("a", href=True)
                    if elem_link:
                        elem_text = elem_link.get_text(strip=True)[:50]
                # Try any text
                if not elem_text:
                    elem_text = elem.get_text(strip=True)[:50]
                
                if elem_text:
                    sample_texts.append(elem_text)
            
            # If all samples are identical, just show one
            unique_samples = list(dict.fromkeys(sample_texts))  # Preserve order
            if len(unique_samples) > 1:
                sample_title = " | ".join(unique_samples)
            elif unique_samples:
                sample_title = unique_samples[0]
            
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
    
    # Strategy 5: URL pattern detection (find links with common path patterns)
    # This is inspired by the FDA connector which uses href pattern matching
    # More resilient to HTML structure changes than class-based selection
    links = soup.find_all("a", href=True)
    if len(links) >= min_items:
        # Group links by URL path patterns
        from urllib.parse import urlparse
        path_patterns = Counter()
        
        for link in links:
            href = link.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            
            # Extract path pattern (ignore specific IDs/slugs)
            try:
                parsed = urlparse(href)
                path = parsed.path
                
                # Convert specific paths to patterns
                # /articles/123/my-slug -> /articles
                # /post/2024/11/09/title -> /post  
                parts = [p for p in path.split("/") if p]
                if len(parts) >= 1:
                    # Keep only first part to find common base paths
                    pattern = "/" + parts[0]
                    path_patterns[pattern] += 1
                elif len(parts) == 0 and path == "/":
                    # Root path
                    path_patterns["/"] += 1
            except Exception:
                continue
        
        # Find most common path pattern
        for pattern, count in path_patterns.most_common(3):
            if count >= min_items:
                # Find links matching this pattern
                matching_links = [
                    link for link in links
                    if link.get("href", "").startswith(pattern)
                ]
                
                if matching_links:
                    # Strategy: Find common parent container of these links
                    # This is more useful than selecting the links themselves
                    parent_containers = []
                    for link in matching_links[:10]:  # Sample first 10
                        # Walk up to find a meaningful container (article, li, div with class, etc.)
                        parent = link.parent
                        depth = 0
                        while parent and depth < 5:
                            # Stop at semantic tags or elements with classes
                            if parent.name in ["article", "li", "tr", "section"]:
                                parent_containers.append(parent)
                                break
                            elif parent.get("class"):
                                parent_containers.append(parent)
                                break
                            parent = parent.parent
                            depth += 1
                    
                    # Find most common parent type
                    if parent_containers:
                        parent_tags = Counter()
                        parent_classes = Counter()
                        
                        for container in parent_containers:
                            parent_tags[container.name] += 1
                            classes = container.get("class", [])
                            if classes:
                                # Use first class as representative
                                parent_classes[f"{container.name}.{classes[0]}"] += 1
                        
                        # Prefer classed containers over bare tags
                        if parent_classes:
                            most_common = parent_classes.most_common(1)[0]
                            selector = most_common[0]
                            count_in_sample = most_common[1]
                            
                            # Find all instances of this container
                            tag_name, class_name = selector.split(".", 1)
                            all_containers = soup.find_all(tag_name, class_=class_name)
                            actual_count = len(all_containers)
                        else:
                            # Fall back to bare tag
                            most_common_tag = parent_tags.most_common(1)[0][0]
                            selector = most_common_tag
                            all_containers = soup.find_all(most_common_tag)
                            actual_count = len(all_containers)
                        
                        # Get sample from first container
                        first_container = all_containers[0] if all_containers else parent_containers[0]
                        
                        # Extract sample title from container
                        sample_title = ""
                        title_elem = first_container.find(["h1", "h2", "h3", "h4", "h5", "h6"])
                        if title_elem:
                            sample_title = title_elem.get_text(strip=True)[:80]
                        elif first_container.find("a", href=True):
                            link_text = first_container.find("a", href=True).get_text(strip=True)
                            sample_title = link_text[:80] if link_text else "Item"
                        else:
                            sample_title = first_container.get_text(strip=True)[:80] or "Item"
                        
                        candidates.append({
                            "selector": selector,
                            "count": actual_count,
                            "sample_title": sample_title,
                            "sample_url": first_container.find("a", href=True).get("href", "") if first_container.find("a", href=True) else "",
                            "confidence": "high" if actual_count >= 10 else "medium",
                        })
                    else:
                        # Fall back to selecting links directly (less useful but better than nothing)
                        selector = f"a[href*='{pattern}']"
                        first_link = matching_links[0]
                        sample_title = first_link.get_text(strip=True)[:80] or "Link"
                        
                        candidates.append({
                            "selector": selector,
                            "count": len(matching_links),
                            "sample_title": sample_title,
                            "sample_url": first_link.get("href", ""),
                            "confidence": "low",  # Links without containers are less useful
                        })
    
    # Strategy 6: Link density clustering
    # Find containers with high link density (likely list items)
    # Look for elements that contain exactly 1-3 links (typical for list items)
    all_elements = soup.find_all(True)
    link_containers = []
    
    for elem in all_elements:
        # Skip if too deep or already counted
        if elem.name in ["html", "head", "body", "script", "style"]:
            continue
        
        # Count direct child links (not nested deeply)
        direct_links = elem.find_all("a", href=True, recursive=False)
        nested_links = elem.find_all("a", href=True)
        
        # Good candidate: has 1-3 links and some text
        if 1 <= len(nested_links) <= 3:
            text = elem.get_text(strip=True)
            if text and len(text) > 10:  # Has substantial text
                link_containers.append(elem)
    
    # Group by tag+class signature
    if link_containers:
        signature_counts = Counter()
        signature_examples = {}
        
        for container in link_containers:
            classes = " ".join(container.get("class", []))
            signature = f"{container.name}.{classes.split()[0]}" if classes else container.name
            signature_counts[signature] += 1
            if signature not in signature_examples:
                signature_examples[signature] = container
        
        for signature, count in signature_counts.items():
            if count >= min_items:
                # Check if not already covered
                if any(sig in c.get("selector", "") for sig in [signature, signature.split(".")[0]] for c in candidates):
                    continue
                
                example = signature_examples[signature]
                sample_title = ""
                
                link = example.find("a", href=True)
                if link:
                    sample_title = link.get_text(strip=True)[:80]
                
                if not sample_title:
                    sample_title = example.get_text(strip=True)[:80] or f"<{signature}> with links"
                
                selector = f".{signature.split('.')[-1]}" if "." in signature else signature
                
                candidates.append({
                    "selector": selector,
                    "count": count,
                    "sample_title": sample_title,
                    "sample_url": link.get("href") if link else "",
                    "confidence": "medium",
                })
    
    # Deduplicate candidates with same selector
    seen_selectors = set()
    unique_candidates = []
    for candidate in candidates:
        if candidate["selector"] not in seen_selectors:
            seen_selectors.add(candidate["selector"])
            unique_candidates.append(candidate)
    
    # Sort by confidence first (high > medium > low), then by count
    def sort_key(candidate):
        confidence_score = {"high": 3, "medium": 2, "low": 1}.get(candidate["confidence"], 0)
        count = candidate["count"]
        
        # Penalize very high counts (likely navigation/chrome elements)
        if count > 50:
            count_score = count / 2
        else:
            count_score = count
        
        # Boost candidates with meaningful sample titles
        has_meaningful_title = (
            candidate.get("sample_title") and 
            not candidate["sample_title"].startswith("Text: '") and
            not candidate["sample_title"].startswith("<") and
            len(candidate["sample_title"]) > 10
        )
        title_boost = 100 if has_meaningful_title else 0
        
        return (confidence_score, title_boost, count_score)
    
    sorted_candidates = sorted(unique_candidates, key=sort_key, reverse=True)
    
    # Return top 25 candidates (more options for user)
    # But filter out obvious non-content elements
    filtered = []
    for candidate in sorted_candidates:
        # Skip if count is suspiciously high and no meaningful title
        if candidate["count"] > 100 and not candidate.get("sample_url"):
            continue
        filtered.append(candidate)
        if len(filtered) >= 25:
            break
    
    return filtered if filtered else sorted_candidates[:25]


def _make_selector_robust(element: Tag, item_element: Tag) -> str:
    """
    Build a robust CSS selector for element relative to item_element.
    
    Handles deep nesting, obfuscated classes, and dynamic class names.
    
    Args:
        element: The target element to select
        item_element: The item container (root context)
    
    Returns:
        Robust CSS selector string
    """
    # Use robust selector builder with item as root
    selector = build_robust_selector(element, root=item_element)
    
    # If selector is just a single class/tag, it's already simple enough
    if " " not in selector and ">" not in selector:
        return selector
    
    # For complex selectors, strip the root marker if present since we're already scoped to item
    # This keeps selectors relative to the item container
    return selector


def generate_field_selector(item_element: Tag, field_type: str) -> str | None:  # noqa: PLR0911, PLR0912, C901
    """
    Generate CSS selector for common field types within an item.
    Uses multiple strategies to handle diverse HTML patterns.
    
    Args:
        item_element: BeautifulSoup Tag representing the item container
        field_type: One of 'title', 'url', 'date', 'author', 'score', 'image'
    
    Returns:
        CSS selector string or None if not found
    """
    if field_type == "title":
        # Strategy 1: Semantic headings (highest priority)
        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            elem = item_element.find(tag)
            if elem and elem.get_text(strip=True):
                classes = elem.get("class", [])
                if classes:
                    return f"{tag}.{classes[0]}"
                return tag
        
        # Strategy 2: Data attributes (common in modern frameworks)
        for attr in ["data-title", "data-name", "data-heading"]:
            elem = item_element.find(attrs={attr: True})
            if elem:
                classes = elem.get("class", [])
                if classes:
                    return f".{classes[0]}"
                return f"[{attr}]"
        
        # Strategy 3: Semantic attributes
        for attr_check in [
            {"itemprop": "name"},
            {"itemprop": "headline"},
            {"role": "heading"},
        ]:
            elem = item_element.find(attrs=attr_check)
            if elem and elem.get_text(strip=True):
                classes = elem.get("class", [])
                if classes:
                    return f".{classes[0]}"
                attr_name = list(attr_check.keys())[0]
                attr_value = list(attr_check.values())[0]
                return f"[{attr_name}='{attr_value}']"
        
        # Strategy 4: Largest text block or container (for split titles or complex structure)
        # Check both direct text and combined child text
        max_text_len = 0
        best_text_elem = None
        
        for elem in item_element.find_all(["span", "div", "p", "strong", "b", "h1", "h2", "h3", "h4", "h5", "h6"]):
            # Get direct text only (not from children)
            direct_text = "".join(elem.find_all(string=True, recursive=False))
            text_len = len(direct_text.strip())
            
            # Also check combined text for containers with multiple children
            if text_len < 10:
                combined_text = elem.get_text(strip=True)
                if len(combined_text) > text_len:
                    text_len = len(combined_text)
            
            if text_len > max_text_len and text_len > 10:
                max_text_len = text_len
                best_text_elem = elem
        
        if best_text_elem:
            classes = best_text_elem.get("class", [])
            if classes:
                # Check if element is deeply nested (5+ levels from item)
                depth = 0
                current = best_text_elem
                while current and current != item_element and depth < 10:
                    depth += 1
                    current = current.parent
                
                # Use robust selector for deep nesting to avoid brittle paths
                if depth >= 5:
                    return _make_selector_robust(best_text_elem, item_element)
                
                return f".{classes[0]}"
            # If no class, return tag name
            return best_text_elem.name
        
        # Strategy 5: Scored link selection (existing, enhanced)
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
            
            # Boost for data attributes
            if any(a.get(attr) for attr in ["data-title", "data-name"]):
                score += 15
            
            # Penalize common navigation/UI patterns
            classes = " ".join(a.get("class", [])).lower()
            if any(word in classes for word in ["vote", "upvote", "reply", "share", "flag", "hide", "button", "btn"]):
                score -= 30
            if any(word in text.lower() for word in ["vote", "reply", "share", "hide", "save", "report", "edit", "delete"]):
                score -= 30
            
            # Penalize if link is tiny (likely icon/button)
            if len(text) < 5 and not any(ord(c) > 127 for c in text):  # Not unicode
                score -= 20
            
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
        # Strategy 1: Data attributes
        for attr in ["data-url", "data-href", "data-link"]:
            elem = item_element.find(attrs={attr: True})
            if elem:
                classes = elem.get("class", [])
                if classes:
                    return f".{classes[0]}::attr({attr})"
                return f"[{attr}]::attr({attr})"
        
        # Strategy 2: Reuse title logic but append ::attr(href)
        title_selector = generate_field_selector(item_element, "title")
        if title_selector:
            # If title selector already has ::attr, don't add it again
            if "::attr" not in title_selector:
                return f"{title_selector}::attr(href)"
    
    elif field_type == "date":
        # Strategy 1: Semantic time element
        time_elem = item_element.find("time")
        if time_elem:
            classes = time_elem.get("class", [])
            if classes:
                return f"time.{classes[0]}"
            return "time"
        
        # Strategy 2: Data attributes
        for attr in ["data-date", "data-time", "data-timestamp", "data-published"]:
            elem = item_element.find(attrs={attr: True})
            if elem:
                classes = elem.get("class", [])
                if classes:
                    return f".{classes[0]}"
                return f"[{attr}]"
        
        # Strategy 3: Datetime attribute (can be on any element)
        datetime_elem = item_element.find(attrs={"datetime": True})
        if datetime_elem:
            classes = datetime_elem.get("class", [])
            if classes:
                return f".{classes[0]}"
            return datetime_elem.name
        
        # Strategy 4: Score elements by date-related signals (works across languages)
        candidates = []
        for elem in item_element.find_all(["span", "div", "p", "small", "time"]):
            score = 0
            text = elem.get_text(strip=True)
            classes = " ".join(elem.get("class", [])).lower()
            
            # Keyword matching (English and common patterns)
            if any(kw in classes for kw in ["date", "time", "timestamp", "posted", "published", "ago", "when", "updated"]):
                score += 30
            
            # Data attribute presence
            if any(elem.get(attr) for attr in ["data-date", "data-time", "data-timestamp"]):
                score += 25
            
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
        # Strategy 1: Semantic attributes
        for attr_check in [
            {"itemprop": "author"},
            {"rel": "author"},
            {"data-author": True},
            {"data-user": True},
        ]:
            author_elem = item_element.find(attrs=attr_check)
            if author_elem:
                classes = author_elem.get("class", [])
                if classes:
                    return f".{classes[0]}"
                # Return attribute selector if no class
                attr_name = list(attr_check.keys())[0]
                if attr_name.startswith("data-"):
                    return f"[{attr_name}]"
                return author_elem.name
        
        # Strategy 2: Score elements by author-related signals
        candidates = []
        for elem in item_element.find_all(["span", "a", "div", "p", "small"]):
            score = 0
            classes = " ".join(elem.get("class", [])).lower()
            text = elem.get_text(strip=True)
            
            # Keyword matching (expand for multilingual)
            if any(kw in classes for kw in ["author", "user", "username", "by", "posted-by", "submitter", "creator", "writer"]):
                score += 30
            
            # Data attribute presence
            if any(elem.get(attr) for attr in ["data-author", "data-user", "data-username"]):
                score += 25
            
            # Text patterns that suggest authorship
            if text.lower().startswith("by ") or text.startswith("@"):
                score += 15
            
            # Penalize very long text (unlikely to be just a username)
            if len(text) > 50:
                score -= 10
            
            # Penalize very short text (likely abbreviation/icon)
            if len(text) < 2:
                score -= 20
            
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
        # Strategy 1: Data attributes
        for attr in ["data-score", "data-points", "data-votes", "data-rating"]:
            elem = item_element.find(attrs={attr: True})
            if elem:
                classes = elem.get("class", [])
                if classes:
                    return f".{classes[0]}"
                return f"[{attr}]"
        
        # Strategy 2: Score elements by voting/scoring signals
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
    if not html or not html.strip():
        return []
    
    if not item_selector or not item_selector.strip():
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    
    try:
        items = soup.select(item_selector)
    except Exception:
        # Invalid selector
        return []
    
    if not items:
        return []
    
    previews = []
    for item in items[:3]:  # Limit to 3 for preview
        data = {}
        for field_name, selector in field_selectors.items():
            if not selector:
                data[field_name] = ""
                continue
                
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
