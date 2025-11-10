"""Drupal Views profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile, _get_element_classes


class DrupalViewsProfile(FrameworkProfile):
    """Drupal Views module - very common for listing pages."""
    
    name = "drupal_views"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Drupal Views by looking for characteristic classes."""
        score = 0
        
        # Check HTML content for views-specific markers
        if "views-row" in html:
            score += 35
        if "views-field" in html:
            score += 25
        if "view-content" in html:
            score += 15
        if "views-table" in html:
            score += 10
        
        # Check item element if provided
        if item_element:
            classes = _get_element_classes(item_element)
            if "views-row" in classes:
                score += 25
            if "views-field" in classes:
                score += 10
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Drupal Views typically uses .views-row or table rows."""
        return [
            ".views-row",
            "tr.views-row-first",
            "tr.even",
            "tr.odd",
            "tbody > tr",
            ".view-content .views-row",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Common Drupal Views field classes."""
        return {
            "title": [
                ".views-field-field-product-description",
                ".views-field-title",
                ".views-field-name",
                ".views-field-field-title",
                ".field-content",
            ],
            "url": [
                ".views-field-field-product-description a::attr(href)",
                ".views-field-title a::attr(href)",
                ".views-field-name a::attr(href)",
                ".views-field-path a::attr(href)",
            ],
            "date": [
                ".views-field-field-date",
                ".views-field-created",
                ".views-field-changed",
                ".views-field-post-date",
            ],
            "published_date": [
                ".views-field-created",
                ".views-field-post-date",
                ".views-field-published",
            ],
            "updated_date": [
                ".views-field-changed",
                ".views-field-updated",
                ".views-field-modified",
            ],
            "author": [
                ".views-field-company-name",
                ".views-field-brand-name",
                ".views-field-name",  # User name field
                ".views-field-uid",
                ".views-field-author",
                ".views-field-field-author",
            ],
            "body": [
                ".views-field-field-recall-reason-description",
                ".views-field-body",
                ".views-field-field-body",
                ".views-field-description",
            ],
            "excerpt": [
                ".views-field-teaser",
                ".views-field-summary",
                ".views-field-excerpt",
            ],
            "content": [
                ".views-field-body",
                ".views-field-field-body",
                ".views-field-content",
            ],
            "image": [
                ".views-field-field-image img",
                ".views-field-field-photo img",
            ],
            "thumbnail": [
                ".views-field-field-thumbnail img",
                ".views-field-field-image-thumbnail img",
            ],
            "category": [
                ".views-field-field-category",
                ".views-field-type",
                ".views-field-field-type",
            ],
            "tags": [
                ".views-field-field-tags",
                ".views-field-taxonomy",
                ".views-field-field-taxonomy-tags",
            ],
            "rating": [
                ".views-field-field-rating",
                ".views-field-vote-average",
            ],
            "location": [
                ".views-field-field-location",
                ".views-field-field-address",
                ".views-field-city",
            ],
            "phone": [
                ".views-field-field-phone",
                ".views-field-field-telephone",
            ],
            "email": [
                ".views-field-field-email",
                ".views-field-mail",
            ],
        }
