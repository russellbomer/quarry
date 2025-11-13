"""Django Admin profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class DjangoAdminProfile(FrameworkProfile):
    """Django Admin interface detection."""
    
    name = "django_admin"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Django Admin by looking for admin-specific classes and meta tags."""
        score = 0
        
        # Django Admin indicators
        if "django-admin" in html:
            score += 40
        if "grp-" in html:  # Django Grappelli
            score += 30
        if "suit-" in html:  # Django Suit
            score += 30
        if "/admin/" in html:
            score += 20
        if "djdt" in html:  # Django Debug Toolbar
            score += 15
        if "field-" in html and "th.field" in html:
            score += 20
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Django Admin list view selectors."""
        return [
            "tbody tr",
            ".result",
            ".grp-row",
            "tr.row1, tr.row2",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Django Admin field mappings."""
        return {
            "title": [
                "th.field-__str__ a",
                ".field-title a",
                ".field-name a",
            ],
            "url": [
                "th.field-__str__ a::attr(href)",
                ".field-title a::attr(href)",
            ],
            "date": [
                ".field-created",
                ".field-modified",
                ".field-date",
                ".field-published",
            ],
            "published_date": [
                ".field-created",
                ".field-published",
                ".field-date_published",
            ],
            "updated_date": [
                ".field-modified",
                ".field-updated",
                ".field-last_modified",
            ],
            "author": [
                ".field-author",
                ".field-user",
                ".field-created_by",
                ".field-owner",
            ],
            "category": [
                ".field-category",
                ".field-type",
            ],
            "tags": [
                ".field-tags",
                ".field-keywords",
            ],
            "status": [
                ".field-status",
                ".field-is_active",
                ".field-published",
            ],
        }
