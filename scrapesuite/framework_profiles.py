"""Framework-specific HTML structure profiles for better field detection."""

from typing import Any

from bs4 import Tag


class FrameworkProfile:
    """Base class for framework-specific detection profiles."""
    
    name: str = "generic"
    
    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect if this framework is being used with confidence scoring.
        
        Args:
            html: Full page HTML
            item_element: Optional item container element
        
        Returns:
            Confidence score (0-100). 0 = not detected, 100 = very confident.
            Threshold for detection is typically 50.
        """
        raise NotImplementedError
    
    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Get CSS selector patterns likely to match item containers.
        
        Returns:
            List of selector patterns to try
        """
        return []
    
    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to CSS selector/class pattern mappings.
        
        Returns:
            Dict mapping field types to list of selector patterns
        """
        return {}
    
    @classmethod
    def generate_field_selector(cls, item_element: Tag, field_type: str) -> str | None:
        """
        Generate field selector using framework-specific knowledge.
        
        Args:
            item_element: Item container element
            field_type: Field type to detect
        
        Returns:
            CSS selector string or None
        """
        mappings = cls.get_field_mappings()
        patterns = mappings.get(field_type, [])
        
        for pattern in patterns:
            # Handle ::attr() syntax for attribute extraction
            has_attr = "::attr(" in pattern
            if has_attr:
                # Split pattern and attr
                base_pattern = pattern.split("::attr(")[0].strip()
                # attr_name = pattern.split("::attr(")[1].rstrip(")")
            else:
                base_pattern = pattern
            
            # Try to find element matching pattern
            if base_pattern.startswith("."):
                # Class selector
                class_name = base_pattern[1:].split()[0]  # Get first class if pattern has spaces
                
                # Handle patterns like ".class a" (selector with descendant)
                if " " in base_pattern:
                    # Split into parent and child
                    parts = base_pattern.split()
                    parent_selector = parts[0][1:]  # Remove leading dot from first part
                    child_selector = " ".join(parts[1:])
                    
                    # Find parent element
                    parent = item_element.find(class_=parent_selector)
                    if parent:
                        # Check if child exists
                        if child_selector == "a":
                            if parent.find("a", href=True):
                                return pattern  # Return original with ::attr if present
                        elif child_selector.startswith("img"):
                            if parent.find("img"):
                                return pattern
                        elif child_selector.startswith("time"):
                            if parent.find("time"):
                                return pattern
                        else:
                            # Try generic tag search
                            if parent.find(child_selector.split()[0]):
                                return pattern
                else:
                    # Simple class selector
                    elem = item_element.find(class_=class_name)
                    if elem:
                        return pattern
            elif base_pattern.count(".") > 0 and not base_pattern.startswith("["):
                # Handle tag.class patterns like "th.field-__str__"
                if " " in base_pattern:
                    # Complex selector with descendants
                    parts = base_pattern.split()
                    first_part = parts[0]
                    
                    # Parse tag.class
                    if "." in first_part:
                        tag_name, class_name = first_part.split(".", 1)
                        parent = item_element.find(tag_name, class_=class_name)
                    else:
                        parent = item_element.find(class_=first_part)
                    
                    if parent:
                        # Check for descendant
                        child_selector = " ".join(parts[1:])
                        if child_selector == "a":
                            if parent.find("a", href=True):
                                return pattern
                        elif parent.find(child_selector.split()[0]):
                            return pattern
                else:
                    # Simple tag.class pattern
                    tag_name, class_name = base_pattern.split(".", 1)
                    elem = item_element.find(tag_name, class_=class_name)
                    if elem:
                        return pattern
            elif base_pattern.startswith("["):
                # Attribute selector - parse it
                # Simple implementation for common cases
                if "*=" in base_pattern:
                    # Partial match selector like [class*='title']
                    attr_name = base_pattern.split("*=")[0].replace("[", "").strip()
                    search_value = base_pattern.split("*=")[1].replace("]", "").replace("'", "").replace('"', "").strip()
                    
                    # Find element with attribute containing value
                    for elem in item_element.find_all():
                        attr_val = elem.get(attr_name, "")
                        if isinstance(attr_val, list):
                            attr_val = " ".join(attr_val)
                        if search_value.lower() in str(attr_val).lower():
                            return pattern
                elif "=" in base_pattern:
                    attr_name = base_pattern.split("=")[0].replace("[", "").strip()
                    elem = item_element.find(attrs={attr_name: True})
                    if elem:
                        return pattern
            else:
                # Tag selector or more complex selector
                # Try to find element by tag name
                elem = item_element.find(base_pattern.split()[0])  # Get first part for tag selectors
                if elem:
                    return pattern
        
        return None


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
            classes = " ".join(item_element.get("class", []))
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
            classes = " ".join(item_element.get("class", []))
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


# Registry of all available profiles
# Order matters: More specific frameworks should come before generic ones
FRAMEWORK_PROFILES: list[type[FrameworkProfile]] = [
    DjangoAdminProfile,     # Very specific (Django admin)
    NextJSProfile,          # Specific (Next.js apps)
    ReactComponentProfile,  # Specific (React apps)
    VueJSProfile,           # Specific (Vue.js apps)
    DrupalViewsProfile,     # Specific CMS
    ShopifyProfile,         # Specific e-commerce
    TailwindProfile,        # Framework/utility CSS
    BootstrapProfile,       # Component library
    WordPressProfile,       # Generic CMS (might match "post" class from others)
]


def detect_framework(html: str, item_element: Tag | None = None) -> type[FrameworkProfile] | None:
    """
    Detect which framework is being used (returns best match above threshold).
    
    Args:
        html: Full page HTML
        item_element: Optional item container element
    
    Returns:
        Detected framework profile class or None if no match above threshold (40)
    """
    best_score = 0
    best_profile = None
    
    for profile_class in FRAMEWORK_PROFILES:
        score = profile_class.detect(html, item_element)
        if score > best_score:
            best_score = score
            best_profile = profile_class
    
    # Return best match if above threshold (lowered to 40 for better detection)
    return best_profile if best_score >= 40 else None


def detect_all_frameworks(html: str, item_element: Tag | None = None) -> list[tuple[type[FrameworkProfile], int]]:
    """
    Detect all frameworks with their confidence scores.
    
    Args:
        html: Full page HTML
        item_element: Optional item container element
    
    Returns:
        List of (profile_class, score) tuples sorted by score (highest first).
        Only includes profiles with score > 0.
    """
    results = []
    
    for profile_class in FRAMEWORK_PROFILES:
        score = profile_class.detect(html, item_element)
        if score > 0:
            results.append((profile_class, score))
    
    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def get_framework_field_selector(
    framework: type[FrameworkProfile],
    item_element: Tag,
    field_type: str,
) -> str | None:
    """
    Get field selector using framework-specific knowledge.
    
    Args:
        framework: Framework profile class
        item_element: Item container element
        field_type: Field type to detect
    
    Returns:
        CSS selector string or None
    """
    return framework.generate_field_selector(item_element, field_type)


def is_framework_pattern(selector: str, framework: type[FrameworkProfile] | None) -> bool:
    """
    Check if a selector matches known framework patterns.
    
    Args:
        selector: CSS selector to check
        framework: Detected framework profile class or None
    
    Returns:
        True if selector matches framework patterns
    """
    if not framework:
        return False
    
    # Check if selector matches any container pattern
    for pattern in framework.get_item_selector_hints():
        if pattern in selector or selector in pattern:
            return True
    
    # Check if selector matches any field mapping pattern
    for field_patterns in framework.get_field_mappings().values():
        for pattern in field_patterns:
            # Remove ::attr() suffix for comparison
            base_pattern = pattern.split("::attr(")[0] if "::attr(" in pattern else pattern
            if base_pattern in selector or selector in base_pattern:
                return True
    
    return False

