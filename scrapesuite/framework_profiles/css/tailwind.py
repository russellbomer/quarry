"""Tailwind CSS profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class TailwindProfile(FrameworkProfile):
    """Tailwind CSS - increasingly popular utility-first framework."""
    
    name = "tailwind"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Tailwind is harder to detect as it uses utility classes.
        Look for common patterns like flex, grid, space-y, etc.
        """
        score = 0
        
        tailwind_patterns = [
            "flex", "grid", "space-y", "gap-", "p-", "m-", 
            "text-", "bg-", "rounded", "shadow", "border-",
            "hover:", "dark:", "sm:", "md:", "lg:"
        ]
        
        # Count pattern matches (need multiple since these are generic)
        matches = sum(1 for pattern in tailwind_patterns if pattern in html)
        
        # Scale score based on matches (need at least 5 for confidence)
        if matches >= 10:
            score = 70
        elif matches >= 8:
            score = 60
        elif matches >= 6:
            score = 50
        elif matches >= 4:
            score = 30
        
        return score
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Tailwind often uses semantic tags with utility classes."""
        return [
            "article",
            "li",
            "div[class*='flex']",
            "div[class*='grid']",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Tailwind uses semantic HTML, so defer to generic detection."""
        return {}
