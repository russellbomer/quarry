"""React profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class ReactComponentProfile(FrameworkProfile):
    """Generic React application detection."""
    
    name = "react"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect React by looking for data-react attributes and root div."""
        score = 0
        
        # React-specific indicators
        if "data-reactroot" in html:
            score += 40
        if "data-react-" in html:
            score += 35
        if "__REACT" in html:
            score += 30
        if 'id="root"' in html:
            score += 20
        if 'id="app"' in html and ("data-react" in html or "React" in html):
            score += 15
        if "react-dom" in html or "react.js" in html:
            score += 25
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Common React component patterns."""
        return [
            "[class*='Card']",
            "[class*='Item']",
            "[class*='Post']",
            "[class*='Article']",
            "article",
            "[data-testid*='item']",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """React component field mappings (typically use PascalCase/camelCase)."""
        return {
            "title": [
                "[class*='Title']",
                "[class*='Heading']",
                "h2",
                "h3",
            ],
            "url": [
                "a[href]::attr(href)",
                "[class*='Link']::attr(href)",
            ],
            "date": [
                "time",
                "[datetime]",
                "[class*='Date']",
                "[class*='Timestamp']",
            ],
            "published_date": [
                "[class*='PublishedDate']",
                "[class*='CreatedAt']",
            ],
            "updated_date": [
                "[class*='UpdatedAt']",
                "[class*='ModifiedDate']",
            ],
            "author": [
                "[class*='Author']",
                "[class*='User']",
                "[class*='Creator']",
            ],
            "description": [
                "[class*='Description']",
                "[class*='Excerpt']",
                "p",
            ],
            "excerpt": [
                "[class*='Excerpt']",
                "[class*='Summary']",
            ],
            "content": [
                "[class*='Content']",
                "[class*='Body']",
            ],
            "image": [
                "img",
                "[class*='Image'] img",
            ],
            "thumbnail": [
                "[class*='Thumbnail'] img",
                "[class*='Thumb'] img",
            ],
            "category": [
                "[class*='Category']",
                "[class*='Tag']",
            ],
            "tags": [
                "[class*='Tags']",
                "[class*='Keywords']",
            ],
            "rating": [
                "[class*='Rating']",
                "[class*='Score']",
            ],
        }
