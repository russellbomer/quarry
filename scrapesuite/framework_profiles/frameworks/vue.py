"""Vue.js profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class VueJSProfile(FrameworkProfile):
    """Vue.js application detection."""
    
    name = "vuejs"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Vue.js by looking for v- directives and Vue-specific attributes."""
        score = 0
        
        # Vue.js indicators
        if "v-for=" in html:
            score += 45  # Increased from 35
        if "v-if=" in html:
            score += 30  # Increased from 25
        if "v-bind:" in html or ":key=" in html:
            score += 25
        if "@click=" in html or "v-on:" in html:
            score += 20
        if "__VUE__" in html:
            score += 30
        if "vue.js" in html.lower() or "vue@" in html:
            score += 25
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Common Vue.js component patterns."""
        return [
            "[class*='card']",
            "[class*='item']",
            "[class*='post']",
            "article",
            "[v-for]",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Vue.js component field mappings (typically use kebab-case or camelCase)."""
        return {
            "title": [
                "[class*='title']",
                "h2",
                "h3",
            ],
            "url": [
                "a[href]::attr(href)",
                "[class*='link']::attr(href)",
            ],
            "date": [
                "time",
                "[datetime]",
                "[class*='date']",
            ],
            "published_date": [
                "[class*='published']",
                "[class*='created']",
            ],
            "updated_date": [
                "[class*='updated']",
                "[class*='modified']",
            ],
            "author": [
                "[class*='author']",
                "[class*='user']",
            ],
            "excerpt": [
                "[class*='excerpt']",
                "[class*='summary']",
            ],
            "content": [
                "[class*='content']",
                "[class*='body']",
            ],
            "image": [
                "img",
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
            ],
            "rating": [
                "[class*='rating']",
                "[class*='score']",
            ],
        }
