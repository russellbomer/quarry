"""
Robust CSS selector builder for complex nested structures.

Handles:
- Deep nesting (10+ levels)
- Dynamic/obfuscated class names
- Unstable DOM structures
"""

from bs4 import Tag


def build_robust_selector(element: Tag, root: Tag | None = None) -> str:
    """
    Build a robust CSS selector that works despite structural changes.
    
    Uses stable markers (semantic tags, stable classes, IDs) and avoids
    relying on exact nesting depth or dynamic class names.
    
    Args:
        element: Target element to select
        root: Container element to build selector from (optional)
    
    Returns:
        CSS selector string
    """
    if not element or not hasattr(element, 'name'):
        return ""
    
    # If element has an ID, that's the most stable selector
    elem_id = element.get("id")
    if elem_id and not _looks_dynamic(elem_id):
        return f"#{elem_id}"
    
    # Build path from root to element using stable markers
    path_parts = []
    current = element
    max_depth = 15  # Prevent infinite loops
    depth = 0
    
    while current and current.name and depth < max_depth:
        depth += 1
        
        # If this is the root, add it and stop
        if root and current == root:
            marker = _get_stable_marker(current)
            if marker and marker not in ["div", "span"]:
                path_parts.insert(0, marker)
            break
        
        # Get stable marker for current element
        marker = _get_stable_marker(current)
        if marker:
            # Skip generic divs/spans without classes (reduces noise in deep nesting)
            if marker not in ["div", "span"]:
                path_parts.insert(0, marker)
            
            # If we found a very stable marker (ID, semantic tag with unique class),
            # we can stop here UNLESS we have a root to reach
            if _is_very_stable(marker) and not root:
                break
        
        current = current.parent
    
    # Join with descendant combinator (space) for flexibility
    # This works even if intermediate elements are added/removed
    if path_parts:
        return " ".join(path_parts)
    
    # Fallback: just the tag name
    return element.name


def _get_stable_marker(element: Tag) -> str | None:
    """
    Get the most stable identifier for an element.
    
    Priority:
    1. Non-dynamic ID
    2. Semantic tag (article, header, nav, etc.)
    3. Stable class name (not hash-like)
    4. Tag name
    """
    # Check for stable ID
    elem_id = element.get("id")
    if elem_id and not _looks_dynamic(elem_id):
        return f"#{elem_id}"
    
    # Semantic tags are very stable
    semantic_tags = {
        "article", "header", "footer", "nav", "aside", "main", 
        "section", "time", "figure", "figcaption"
    }
    
    if element.name in semantic_tags:
        # Combine with stable class if available
        classes = element.get("class", [])
        stable_classes = [c for c in classes if not _looks_dynamic(c)]
        if stable_classes:
            return f"{element.name}.{stable_classes[0]}"
        return element.name
    
    # Look for stable class names
    classes = element.get("class", [])
    stable_classes = [c for c in classes if not _looks_dynamic(c)]
    
    if stable_classes:
        # Prefer semantic class names
        semantic_keywords = [
            "title", "heading", "content", "article", "post", "item",
            "container", "wrapper", "card", "list", "meta", "author", "date"
        ]
        
        for cls in stable_classes:
            if any(keyword in cls.lower() for keyword in semantic_keywords):
                return f".{cls}"
        
        # Return first stable class
        return f".{stable_classes[0]}"
    
    # Fallback: tag name with nth-of-type if needed
    # (but only for common container tags)
    if element.name in ["div", "span", "li", "tr", "td"]:
        # Check if there are siblings with same tag
        siblings = [s for s in element.parent.children if hasattr(s, 'name') and s.name == element.name]
        if len(siblings) > 1:
            index = siblings.index(element) + 1  # nth-of-type is 1-indexed
            return f"{element.name}:nth-of-type({index})"
    
    return element.name


def _looks_dynamic(name: str) -> bool:
    """
    Check if a class/ID name looks dynamically generated.
    
    Examples of dynamic names:
    - Random hashes: "css-1a2b3c4", "sc-1x2y3z"
    - UUIDs: "elem-550e8400-e29b-41d4"
    - Build artifacts: "jsx-2871293847"
    """
    if not name:
        return True
    
    # Very short names are often dynamic
    if len(name) < 3:
        return True
    
    # Check for common dynamic prefixes
    dynamic_prefixes = ["css-", "sc-", "jsx-", "styled-", "emotion-", "MuiBox-"]
    if any(name.startswith(prefix) for prefix in dynamic_prefixes):
        return True
    
    # Count hex-like segments (common in hashes)
    import re
    hex_segments = re.findall(r'[0-9a-f]{6,}', name.lower())
    if hex_segments:
        return True
    
    # UUID pattern
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', name.lower()):
        return True
    
    # Long numeric suffixes often dynamic
    if re.search(r'-?\d{8,}$', name):
        return True
    
    return False


def _is_very_stable(marker: str) -> bool:
    """Check if a marker is very stable (can stop path building)."""
    # IDs are very stable
    if marker.startswith("#"):
        return True
    
    # Semantic tags with specific classes are stable
    semantic_tags = ["article", "header", "footer", "nav", "main"]
    if any(marker.startswith(tag) for tag in semantic_tags) and "." in marker:
        return True
    
    return False


def simplify_selector(selector: str) -> str:
    """
    Simplify a selector by removing redundant parts.
    
    Example: "div.container > div > div > a" -> ".container a"
    """
    parts = selector.split()
    
    # Remove generic divs and spans
    filtered = []
    for part in parts:
        if part in [">", "+"]:
            continue  # Remove direct child combinators
        if part in ["div", "span"]:
            continue  # Remove generic tags
        
        # Remove tag from tag.class patterns (keep just .class)
        if "." in part and not part.startswith("."):
            # "div.container" -> ".container"
            parts_split = part.split(".", 1)
            if parts_split[0] in ["div", "span"]:
                filtered.append(f".{parts_split[1]}")
            else:
                filtered.append(part)
        else:
            filtered.append(part)
    
    # Return simplified selector
    return " ".join(filtered) if filtered else selector
