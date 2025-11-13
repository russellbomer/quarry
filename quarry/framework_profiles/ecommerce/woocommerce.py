"""WooCommerce e-commerce profile for WordPress product pages."""

from bs4 import Tag

from quarry.framework_profiles.base import FrameworkProfile


class WooCommerceProfile(FrameworkProfile):
    """
    Detect WooCommerce (WordPress e-commerce plugin).
    
    WooCommerce is used by 28% of all e-commerce sites.
    It adds specific classes and structure to WordPress for products.
    """

    name = "woocommerce"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect WooCommerce with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # Strong WooCommerce indicators
        if "woocommerce" in html:
            score += 30  # Class or namespace
        if ".woocommerce " in html or "class=\"woocommerce" in html:
            score += 20  # Actual class usage

        # Product-specific classes
        if "product-card" in html or "wc-product" in html:
            score += 25
        if "woocommerce-loop-product" in html:
            score += 30  # Product loop class
        if "product_title" in html or "woocommerce-product-title" in html:
            score += 20

        # WooCommerce scripts/assets
        if "wc-" in html or "woocommerce.js" in html or "woocommerce.min.js" in html:
            score += 15

        # Price elements
        if "woocommerce-Price-amount" in html:
            score += 25
        if "price" in html and ("amount" in html or "currency" in html):
            score += 10

        # Add to cart elements
        if "add_to_cart" in html or "add-to-cart" in html:
            score += 15

        # Check for WordPress + WooCommerce combination
        if ("wp-content" in html or "wp-includes" in html) and "woocommerce" in html:
            score += 20  # Boost if both WordPress and WooCommerce detected

        return score

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Get CSS selector patterns likely to match WooCommerce products.

        Returns:
            List of selector patterns to try
        """
        return [
            ".product",
            ".woocommerce-loop-product",
            "li.product",
            ".product-card",
            ".wc-product",
            "article.product",
            ".products .product",
            ".woocommerce .product",
            "[class*='product-item']",
        ]

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to WooCommerce class/selector mappings.

        Returns:
            Dict mapping field types to list of selector patterns
        """
        return {
            # Product title
            "title": [
                ".woocommerce-loop-product__title",
                ".product_title",
                "h2.woocommerce-loop-product__title",
                "h1.product_title",
                ".wc-product-title",
                ".product-title",
                "h3.product-title",
            ],
            # Product link
            "link": [
                "a.woocommerce-LoopProduct-link::attr(href)",
                ".woocommerce-loop-product__link::attr(href)",
                ".product-link::attr(href)",
                "a::attr(href)",  # Generic fallback within product
            ],
            "url": [
                "a.woocommerce-LoopProduct-link::attr(href)",
                ".woocommerce-loop-product__link::attr(href)",
                ".product-link::attr(href)",
                "a::attr(href)",  # Generic fallback within product
            ],
            # Product image
            "image": [
                ".woocommerce-product-gallery__image img::attr(src)",
                ".attachment-woocommerce_thumbnail::attr(src)",
                ".product-image img::attr(src)",
                ".woocommerce-loop-product__image img::attr(src)",
                "img.wp-post-image::attr(src)",
            ],
            # Price
            "price": [
                ".woocommerce-Price-amount",
                ".price .amount",
                "span.price",
                ".woocommerce-Price-amount bdi",
                ".price ins .amount",  # Sale price
                ".product-price",
            ],
            # Description/Excerpt
            "description": [
                ".woocommerce-product-details__short-description",
                ".product-excerpt",
                ".wc-product-description",
                "div[itemprop='description']",
                ".product-short-description",
            ],
            # Category
            "category": [
                ".product_cat",
                ".posted_in a",
                "[rel='tag']",
                ".woocommerce-breadcrumb a",
            ],
            # Rating
            "rating": [
                ".star-rating",
                ".woocommerce-product-rating .star-rating",
                "[class*='rating']::attr(aria-label)",
                ".rating-count",
            ],
            # SKU (Stock Keeping Unit)
            "sku": [
                ".sku",
                "span.sku",
                "[itemprop='sku']",
            ],
            # Stock status
            "stock": [
                ".stock",
                ".availability",
                ".in-stock",
                ".out-of-stock",
                "p.stock",
            ],
            # Sale badge
            "sale_badge": [
                ".onsale",
                "span.onsale",
                ".sale-badge",
            ],
        }
