"""Shopify profile for framework detection."""

from bs4 import Tag

from ..base import FrameworkProfile


class ShopifyProfile(FrameworkProfile):
    """Shopify e-commerce platform."""
    
    name = "shopify"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """Detect Shopify by looking for product/collection classes."""
        score = 0
        
        # Shopify-specific indicators
        if "product-" in html:
            score += 30
        if "collection-" in html:
            score += 25
        if "shopify" in html.lower():
            score += 25
        if "cart" in html and "product" in html:
            score += 10
        if "variant" in html:
            score += 10
        
        return min(score, 100)
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """Shopify product selectors."""
        return [
            ".product-card",
            ".product-item",
            ".grid-product",
            ".collection-item",
        ]
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """Common Shopify product fields."""
        return {
            "title": [
                ".product-card__title",
                ".product-title",
                ".grid-product__title",
            ],
            "url": [
                ".product-card__title a",
                ".product-link",
                ".grid-product__link::attr(href)",
            ],
            "price": [
                ".product-price",
                ".price",
                ".grid-product__price",
                ".money",
            ],
            "image": [
                ".product-card__image img",
                ".grid-product__image img",
                ".product-featured-img",
            ],
            "thumbnail": [
                ".product-card__image img",
                ".product-thumbnail",
            ],
            "category": [
                ".product-type",
                ".collection-title",
            ],
            "tags": [
                ".product-tags",
                ".product-tag",
            ],
            "rating": [
                ".spr-badge",
                ".product-rating",
            ],
            "description": [
                ".product-description",
                ".product-card__description",
            ],
            "vendor": [
                ".product-vendor",
                ".grid-product__vendor",
            ],
        }
