"""Next.js profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class NextJSProfile(FrameworkProfile):
    """Next.js application detection."""
    
    name = "nextjs"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Next.js by looking for __NEXT_DATA__ and Next.js-specific attributes."""
        score = 0
        
        # Next.js indicators
        if "__NEXT_DATA__" in html:
            score += 50
        if "__next" in html:
            score += 30
        if "data-nextjs" in html:
            score += 25
        if "/_next/" in html:
            score += 20
        if "next/script" in html or "next/image" in html:
            score += 15
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Common Next.js component patterns."""
        return [
            "[class*='card']",
            "[class*='item']",
            "[class*='post']",
            "article",
            "[data-item]",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Next.js typically uses modular CSS or Tailwind - look for semantic patterns."""
        return {
            "title": [
                "h2 a",
                "h3 a",
                "[class*='title']",
                "[class*='heading']",
            ],
            "url": [
                "a[href^='/']::attr(href)",
                "[class*='link']::attr(href)",
            ],
            "date": [
                "time",
                "[datetime]",
                "[class*='date']",
            ],
            "published_date": [
                "time[datetime]",
                "[class*='published']",
            ],
            "updated_date": [
                "[class*='updated']",
                "[class*='modified']",
            ],
            "author": [
                "[class*='author']",
                "[rel='author']",
                "[class*='user']",
            ],
            "excerpt": [
                "[class*='excerpt']",
                "[class*='summary']",
                "[class*='description']",
            ],
            "content": [
                "[class*='content']",
                "[class*='body']",
            ],
            "image": [
                "img[src]",
                "[class*='image'] img",
            ],
            "thumbnail": [
                "[class*='thumb'] img",
                "[class*='thumbnail'] img",
            ],
            "category": [
                "[class*='category']",
                "[class*='tag']",
            ],
            "tags": [
                "[class*='tags']",
                "[class*='keywords']",
            ],
        }
