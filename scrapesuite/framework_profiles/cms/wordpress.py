"""WordPress profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile, _get_element_classes


class WordPressProfile(FrameworkProfile):
    """WordPress - extremely common CMS."""
    
    name = "wordpress"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect WordPress by looking for characteristic classes."""
        score = 0
        
        # Check for WordPress-specific indicators
        if "wp-content" in html:
            score += 30
        if "post-" in html:
            score += 20
        if "entry-" in html:
            score += 20
        if "hentry" in html:
            score += 15
        if "wp-includes" in html:
            score += 15
        
        # Check item element
        if item_element:
            classes = _get_element_classes(item_element)
            if any(indicator in classes for indicator in ["post", "entry", "hentry", "article"]):
                score += 20
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """WordPress post/article selectors."""
        return [
            "article.post",
            ".post",
            ".hentry",
            "article.hentry",
            ".entry",
            ".type-post",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Common WordPress classes."""
        return {
            "title": [
                ".entry-title",
                ".post-title",
                "h2.entry-title",
                "h1.entry-title",
            ],
            "url": [
                ".entry-title a",
                ".post-title a",
            ],
            "date": [
                ".entry-date",
                ".post-date",
                ".published",
                "time.entry-date",
            ],
            "published_date": [
                ".published",
                ".entry-date",
                "time.published",
            ],
            "updated_date": [
                ".updated",
                ".modified",
                "time.updated",
            ],
            "author": [
                ".author",
                ".entry-author",
                ".post-author",
                ".by-author",
                ".vcard",
            ],
            "body": [
                ".entry-content",
                ".post-content",
            ],
            "excerpt": [
                ".entry-summary",
                ".entry-excerpt",
                ".post-excerpt",
            ],
            "content": [
                ".entry-content",
                ".post-content",
                ".article-content",
            ],
            "image": [
                ".post-thumbnail img",
                ".entry-image img",
                ".wp-post-image",
            ],
            "thumbnail": [
                ".post-thumbnail img",
                ".attachment-thumbnail",
            ],
            "category": [
                ".cat-links",
                ".entry-categories",
                ".post-categories",
            ],
            "tags": [
                ".tag-links",
                ".entry-tags",
                ".post-tags",
            ],
            "rating": [
                ".star-rating",
                ".rating",
            ],
            "phone": [
                ".phone",
                ".tel",
            ],
            "email": [
                ".email",
                ".mail",
            ],
        }
