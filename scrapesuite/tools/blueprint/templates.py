"""Schema templates for common data extraction patterns."""

from scrapesuite.lib.schemas import ExtractionSchema, FieldSchema


# Template definitions
TEMPLATES = {
    "article": {
        "name": "Article Extraction",
        "description": "Extract news articles, blog posts, or editorial content",
        "common_selectors": ["article", ".post", ".article", ".entry", ".story"],
        "fields": {
            "title": FieldSchema(
                selector="h1, h2, .title, .headline",
                required=True
            ),
            "link": FieldSchema(
                selector="a",
                attribute="href",
                required=True
            ),
            "author": FieldSchema(
                selector=".author, .byline, address",
                required=False
            ),
            "date": FieldSchema(
                selector="time, .date, .published",
                attribute="datetime",
                required=False
            ),
            "description": FieldSchema(
                selector="p, .summary, .excerpt, .description",
                required=False
            ),
            "image": FieldSchema(
                selector="img",
                attribute="src",
                required=False
            ),
            "category": FieldSchema(
                selector=".category, .tag, .section",
                required=False
            ),
        }
    },
    
    "product": {
        "name": "Product Listing",
        "description": "Extract e-commerce products with pricing",
        "common_selectors": [".product", ".item", ".card", "li.product-item"],
        "fields": {
            "name": FieldSchema(
                selector="h2, h3, .title, .name, .product-name",
                required=True
            ),
            "link": FieldSchema(
                selector="a",
                attribute="href",
                required=True
            ),
            "price": FieldSchema(
                selector=".price, .cost, .amount, .current-price",
                required=True
            ),
            "image": FieldSchema(
                selector="img",
                attribute="src",
                required=False
            ),
            "description": FieldSchema(
                selector=".description, .summary, p",
                required=False
            ),
            "rating": FieldSchema(
                selector=".rating, .stars, .review-score",
                required=False
            ),
            "availability": FieldSchema(
                selector=".stock, .availability, .in-stock",
                required=False
            ),
            "brand": FieldSchema(
                selector=".brand, .manufacturer",
                required=False
            ),
        }
    },
    
    "event": {
        "name": "Event Listing",
        "description": "Extract events, conferences, or scheduled activities",
        "common_selectors": [".event", ".activity", ".listing", "article.event"],
        "fields": {
            "title": FieldSchema(
                selector="h2, h3, .title, .name",
                required=True
            ),
            "link": FieldSchema(
                selector="a",
                attribute="href",
                required=False
            ),
            "date": FieldSchema(
                selector="time, .date, .event-date",
                attribute="datetime",
                required=True
            ),
            "time": FieldSchema(
                selector=".time, .event-time",
                required=False
            ),
            "location": FieldSchema(
                selector=".location, .venue, .place",
                required=False
            ),
            "description": FieldSchema(
                selector="p, .description, .summary",
                required=False
            ),
            "price": FieldSchema(
                selector=".price, .cost, .fee",
                required=False
            ),
            "organizer": FieldSchema(
                selector=".organizer, .host",
                required=False
            ),
        }
    },
    
    "job": {
        "name": "Job Posting",
        "description": "Extract job listings and career opportunities",
        "common_selectors": [".job", ".position", ".listing", "article.job-posting"],
        "fields": {
            "title": FieldSchema(
                selector="h2, h3, .title, .job-title",
                required=True
            ),
            "link": FieldSchema(
                selector="a",
                attribute="href",
                required=True
            ),
            "company": FieldSchema(
                selector=".company, .employer, .organization",
                required=True
            ),
            "location": FieldSchema(
                selector=".location, .city, .place",
                required=False
            ),
            "salary": FieldSchema(
                selector=".salary, .compensation, .pay",
                required=False
            ),
            "description": FieldSchema(
                selector="p, .description, .summary",
                required=False
            ),
            "date_posted": FieldSchema(
                selector="time, .date, .posted",
                attribute="datetime",
                required=False
            ),
            "job_type": FieldSchema(
                selector=".type, .employment-type, .category",
                required=False
            ),
        }
    },
    
    "recipe": {
        "name": "Recipe",
        "description": "Extract cooking recipes with ingredients and instructions",
        "common_selectors": [".recipe", "article.recipe", ".recipe-card"],
        "fields": {
            "title": FieldSchema(
                selector="h1, h2, .title, .recipe-name",
                required=True
            ),
            "link": FieldSchema(
                selector="a",
                attribute="href",
                required=False
            ),
            "image": FieldSchema(
                selector="img",
                attribute="src",
                required=False
            ),
            "description": FieldSchema(
                selector="p, .description, .summary",
                required=False
            ),
            "prep_time": FieldSchema(
                selector=".prep-time, .preptime, time[itemprop='prepTime']",
                required=False
            ),
            "cook_time": FieldSchema(
                selector=".cook-time, .cooktime, time[itemprop='cookTime']",
                required=False
            ),
            "servings": FieldSchema(
                selector=".servings, .yield, [itemprop='recipeYield']",
                required=False
            ),
            "author": FieldSchema(
                selector=".author, .chef, [itemprop='author']",
                required=False
            ),
        }
    },
    
    "review": {
        "name": "Review/Testimonial",
        "description": "Extract user reviews and testimonials",
        "common_selectors": [".review", ".testimonial", ".comment", "article.review"],
        "fields": {
            "title": FieldSchema(
                selector="h3, h4, .title, .review-title",
                required=False
            ),
            "author": FieldSchema(
                selector=".author, .reviewer, .username",
                required=True
            ),
            "rating": FieldSchema(
                selector=".rating, .stars, .score",
                required=True
            ),
            "date": FieldSchema(
                selector="time, .date, .posted",
                attribute="datetime",
                required=False
            ),
            "content": FieldSchema(
                selector="p, .content, .text, .body",
                required=True
            ),
            "verified": FieldSchema(
                selector=".verified, .verified-purchase",
                required=False
            ),
            "helpful_count": FieldSchema(
                selector=".helpful, .votes, .likes",
                required=False
            ),
        }
    },
    
    "person": {
        "name": "Person/Profile",
        "description": "Extract people profiles or directory listings",
        "common_selectors": [".person", ".profile", ".team-member", ".contact"],
        "fields": {
            "name": FieldSchema(
                selector="h2, h3, .name, .fullname",
                required=True
            ),
            "title": FieldSchema(
                selector=".title, .position, .role",
                required=False
            ),
            "image": FieldSchema(
                selector="img",
                attribute="src",
                required=False
            ),
            "email": FieldSchema(
                selector="a[href^='mailto:']",
                attribute="href",
                required=False
            ),
            "phone": FieldSchema(
                selector=".phone, .tel, a[href^='tel:']",
                required=False
            ),
            "bio": FieldSchema(
                selector="p, .bio, .description",
                required=False
            ),
            "organization": FieldSchema(
                selector=".company, .organization",
                required=False
            ),
            "link": FieldSchema(
                selector="a.profile-link",
                attribute="href",
                required=False
            ),
        }
    },
}


def get_template(template_name: str) -> dict:
    """
    Get a schema template by name.
    
    Args:
        template_name: Name of the template (e.g., 'article', 'product')
    
    Returns:
        Template dictionary with metadata and fields
    
    Raises:
        KeyError: If template not found
    """
    return TEMPLATES[template_name]


def list_templates() -> list[dict]:
    """
    List all available templates.
    
    Returns:
        List of template info (name, description)
    """
    return [
        {
            "key": key,
            "name": template["name"],
            "description": template["description"],
        }
        for key, template in TEMPLATES.items()
    ]


def create_from_template(
    template_name: str,
    schema_name: str,
    url: str | None = None,
    item_selector: str | None = None,
    custom_fields: dict[str, FieldSchema] | None = None
) -> ExtractionSchema:
    """
    Create an extraction schema from a template.
    
    Args:
        template_name: Name of the template to use
        schema_name: Name for the new schema
        url: Optional target URL
        item_selector: Optional custom item selector (uses template default if not provided)
        custom_fields: Optional additional fields to add/override
    
    Returns:
        ExtractionSchema instance
    """
    template = get_template(template_name)
    
    # Use custom selector or template default
    if not item_selector:
        item_selector = template["common_selectors"][0]
    
    # Start with template fields
    fields = dict(template["fields"])
    
    # Merge custom fields
    if custom_fields:
        fields.update(custom_fields)
    
    return ExtractionSchema(
        name=schema_name,
        description=template["description"],
        url=url,
        item_selector=item_selector,
        fields=fields
    )


def suggest_template(detected_fields: list[str]) -> str | None:
    """
    Suggest a template based on detected field names.
    
    Args:
        detected_fields: List of field names detected in the page
    
    Returns:
        Template key that best matches, or None
    """
    field_set = set(f.lower() for f in detected_fields)
    
    # Score each template
    scores = {}
    for key, template in TEMPLATES.items():
        template_fields = set(template["fields"].keys())
        # How many template fields are in detected fields
        overlap = len(field_set & template_fields)
        if overlap > 0:
            scores[key] = overlap
    
    # Return template with highest score
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]
    
    return None
