"""Bootstrap profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class BootstrapProfile(FrameworkProfile):
    """Bootstrap framework - very common for cards/listings."""
    
    name = "bootstrap"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Bootstrap by looking for characteristic classes."""
        score = 0
        
        # Bootstrap component indicators
        if "card" in html:
            score += 25
        if "list-group-item" in html:
            score += 25
        if "media" in html:
            score += 15
        if "row" in html and "col" in html:
            score += 15
        if "btn-" in html:
            score += 10
        if "container" in html:
            score += 10
        
        # Check item element
        if item_element:
            classes = " ".join(item_element.get("class", []))
            if any(indicator in classes for indicator in ["card", "list-group-item", "media"]):
                score += 20
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Bootstrap component selectors."""
        return [
            ".card",
            ".list-group-item",
            ".media",
            ".row .col",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Common Bootstrap patterns."""
        return {
            "title": [
                ".card-title",
                ".media-heading",
                "h5.card-title",
                ".list-group-item-heading",
            ],
            "url": [
                ".card-title a",
                ".card-link",
                ".list-group-item[href]::attr(href)",
            ],
            "date": [
                ".card-subtitle",
                ".text-muted",
                "small.text-muted",
            ],
            "author": [
                ".card-footer",
                ".media-heading small",
            ],
            "body": [
                ".card-text",
                ".card-body",
            ],
            "excerpt": [
                ".card-text",
                ".list-group-item-text",
            ],
            "content": [
                ".card-body",
                ".media-body",
            ],
            "image": [
                ".card-img-top",
                ".media-object",
                "img.rounded",
            ],
            "thumbnail": [
                ".card-img-top",
                "img.img-thumbnail",
            ],
            "category": [
                ".badge",
                ".label",
            ],
            "tags": [
                ".badge-pill",
                ".tag",
            ],
            "rating": [
                ".star-rating",
                ".rating",
            ],
        }
