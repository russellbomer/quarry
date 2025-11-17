"""Schema templates for common data extraction patterns."""

from quarry.lib.schemas import FieldSchema

# Template definitions
TEMPLATES = {
    "article": {
        "name": "Article Extraction",
        "description": "Extract news articles, blog posts, or editorial content",
        "common_selectors": ["article", ".post", ".article", ".entry", ".story"],
        "fields": {
            "title": FieldSchema(selector="h1, h2, .title, .headline", required=True),
            "link": FieldSchema(selector="a", attribute="href", required=True),
            "author": FieldSchema(selector=".author, .byline, address", required=False),
            "date": FieldSchema(
                selector="time, .date, .published", attribute="datetime", required=False
            ),
            "description": FieldSchema(
                selector="p, .summary, .excerpt, .description", required=False
            ),
            "image": FieldSchema(selector="img", attribute="src", required=False),
            "category": FieldSchema(selector=".category, .tag, .section", required=False),
        },
    },
    "product": {
        "name": "Product Listing",
        "description": "Extract e-commerce products with pricing",
        "common_selectors": [".product", ".item", ".card", "li.product-item"],
        "fields": {
            "name": FieldSchema(selector="h2, h3, .title, .name, .product-name", required=True),
            "link": FieldSchema(selector="a", attribute="href", required=True),
            "price": FieldSchema(selector=".price, .cost, .amount, .current-price", required=True),
            "image": FieldSchema(selector="img", attribute="src", required=False),
            "description": FieldSchema(selector=".description, .summary, p", required=False),
            "rating": FieldSchema(selector=".rating, .stars, .review-score", required=False),
            "availability": FieldSchema(
                selector=".stock, .availability, .in-stock", required=False
            ),
            "brand": FieldSchema(selector=".brand, .manufacturer", required=False),
        },
    },
    "event": {
        "name": "Event Listing",
        "description": "Extract events, conferences, or scheduled activities",
        "common_selectors": [".event", ".activity", ".listing", "article.event"],
        "fields": {
            "title": FieldSchema(selector="h2, h3, .title, .name", required=True),
            "link": FieldSchema(selector="a", attribute="href", required=False),
            "date": FieldSchema(
                selector="time, .date, .event-date", attribute="datetime", required=True
            ),
            "time": FieldSchema(selector=".time, .event-time", required=False),
            "location": FieldSchema(selector=".location, .venue, .place", required=False),
            "description": FieldSchema(selector="p, .description, .summary", required=False),
            "price": FieldSchema(selector=".price, .cost, .fee", required=False),
            "organizer": FieldSchema(selector=".organizer, .host", required=False),
        },
    },
    "job": {
        "name": "Job Posting",
        "description": "Extract job listings and career opportunities",
        "common_selectors": [".job", ".position", ".listing", "article.job-posting"],
        "fields": {
            "title": FieldSchema(selector="h2, h3, .title, .job-title", required=True),
            "link": FieldSchema(selector="a", attribute="href", required=True),
            "company": FieldSchema(selector=".company, .employer, .organization", required=True),
            "location": FieldSchema(selector=".location, .city, .place", required=False),
            "salary": FieldSchema(selector=".salary, .compensation, .pay", required=False),
            "description": FieldSchema(selector="p, .description, .summary", required=False),
            "date_posted": FieldSchema(
                selector="time, .date, .posted", attribute="datetime", required=False
            ),
            "job_type": FieldSchema(selector=".type, .employment-type, .category", required=False),
        },
    },
    "recipe": {
        "name": "Recipe",
        "description": "Extract cooking recipes with ingredients and instructions",
        "common_selectors": [".recipe", "article.recipe", ".recipe-card"],
        "fields": {
            "title": FieldSchema(selector="h1, h2, .title, .recipe-name", required=True),
            "link": FieldSchema(selector="a", attribute="href", required=False),
            "image": FieldSchema(selector="img", attribute="src", required=False),
            "description": FieldSchema(selector="p, .description, .summary", required=False),
            "prep_time": FieldSchema(
                selector=".prep-time, .preptime, time[itemprop='prepTime']", required=False
            ),
            "cook_time": FieldSchema(
                selector=".cook-time, .cooktime, time[itemprop='cookTime']", required=False
            ),
            "servings": FieldSchema(
                selector=".servings, .yield, [itemprop='recipeYield']", required=False
            ),
            "author": FieldSchema(selector=".author, .chef, [itemprop='author']", required=False),
        },
    },
    "review": {
        "name": "Review/Testimonial",
        "description": "Extract user reviews and testimonials",
        "common_selectors": [".review", ".testimonial", ".comment", "article.review"],
        "fields": {
            "title": FieldSchema(selector="h3, h4, .title, .review-title", required=False),
            "author": FieldSchema(selector=".author, .reviewer, .username", required=True),
            "rating": FieldSchema(selector=".rating, .stars, .score", required=True),
            "date": FieldSchema(
                selector="time, .date, .posted", attribute="datetime", required=False
            ),
            "content": FieldSchema(selector="p, .content, .text, .body", required=True),
            "verified": FieldSchema(selector=".verified, .verified-purchase", required=False),
            "helpful_count": FieldSchema(selector=".helpful, .votes, .likes", required=False),
        },
    },
    "person": {
        "name": "Person/Profile",
        "description": "Extract people profiles or directory listings",
        "common_selectors": [".person", ".profile", ".team-member", ".contact"],
        "fields": {
            "name": FieldSchema(selector="h2, h3, .name, .fullname", required=True),
            "title": FieldSchema(selector=".title, .position, .role", required=False),
            "image": FieldSchema(selector="img", attribute="src", required=False),
            "email": FieldSchema(selector="a[href^='mailto:']", attribute="href", required=False),
            "phone": FieldSchema(selector=".phone, .tel, a[href^='tel:']", required=False),
            "bio": FieldSchema(selector="p, .bio, .description", required=False),
            "organization": FieldSchema(selector=".company, .organization", required=False),
            "link": FieldSchema(selector="a.profile-link", attribute="href", required=False),
        },
    },
    # Business Intelligence Templates
    "financial_data": {
        "name": "Financial Data",
        "description": "Extract financial metrics, stock data, or market information",
        "common_selectors": [".stock", ".ticker", ".financial-data", "tr.data-row"],
        "fields": {
            "symbol": FieldSchema(selector=".symbol, .ticker, .stock-symbol", required=True),
            "company_name": FieldSchema(selector=".name, .company, h3", required=False),
            "price": FieldSchema(selector=".price, .current-price, .last-price", required=True),
            "change": FieldSchema(selector=".change, .price-change", required=False),
            "change_percent": FieldSchema(
                selector=".change-percent, .percent-change", required=False
            ),
            "volume": FieldSchema(selector=".volume, .trading-volume", required=False),
            "market_cap": FieldSchema(
                selector=".market-cap, .cap, .capitalization", required=False
            ),
            "timestamp": FieldSchema(
                selector="time, .timestamp, .updated", attribute="datetime", required=False
            ),
        },
    },
    "real_estate": {
        "name": "Real Estate Listing",
        "description": "Extract property listings and real estate data",
        "common_selectors": [".property", ".listing", ".real-estate-item", "article.property"],
        "fields": {
            "address": FieldSchema(
                selector=".address, .location, .property-address", required=True
            ),
            "price": FieldSchema(selector=".price, .asking-price, .list-price", required=True),
            "bedrooms": FieldSchema(selector=".beds, .bedrooms, .bed-count", required=False),
            "bathrooms": FieldSchema(selector=".baths, .bathrooms, .bath-count", required=False),
            "square_feet": FieldSchema(selector=".sqft, .square-feet, .area", required=False),
            "property_type": FieldSchema(
                selector=".type, .property-type, .category", required=False
            ),
            "image": FieldSchema(selector="img", attribute="src", required=False),
            "link": FieldSchema(selector="a", attribute="href", required=False),
            "listing_date": FieldSchema(
                selector="time, .date, .listed", attribute="datetime", required=False
            ),
            "agent": FieldSchema(selector=".agent, .broker, .listing-agent", required=False),
        },
    },
    "company_directory": {
        "name": "Company Directory",
        "description": "Extract company listings, business directories, or vendor catalogs",
        "common_selectors": [".company", ".business", ".vendor", ".directory-item"],
        "fields": {
            "company_name": FieldSchema(selector="h2, h3, .name, .company-name", required=True),
            "industry": FieldSchema(selector=".industry, .sector, .category", required=False),
            "location": FieldSchema(selector=".location, .address, .city", required=False),
            "website": FieldSchema(
                selector="a.website, a[href^='http']", attribute="href", required=False
            ),
            "phone": FieldSchema(selector=".phone, .tel, a[href^='tel:']", required=False),
            "email": FieldSchema(selector="a[href^='mailto:']", attribute="href", required=False),
            "description": FieldSchema(selector="p, .description, .about", required=False),
            "employees": FieldSchema(selector=".employees, .headcount, .size", required=False),
            "founded": FieldSchema(selector=".founded, .established, .year", required=False),
            "revenue": FieldSchema(selector=".revenue, .sales, .annual-revenue", required=False),
        },
    },
    "analytics_metrics": {
        "name": "Analytics/Metrics Dashboard",
        "description": "Extract KPIs, metrics, and performance indicators",
        "common_selectors": [".metric", ".kpi", ".stat", ".analytics-item", "tr.metric-row"],
        "fields": {
            "metric_name": FieldSchema(selector=".name, .label, .metric-name, th", required=True),
            "value": FieldSchema(selector=".value, .number, .metric-value, td", required=True),
            "unit": FieldSchema(selector=".unit, .metric-unit", required=False),
            "change": FieldSchema(selector=".change, .delta, .variance", required=False),
            "trend": FieldSchema(selector=".trend, .direction, .arrow", required=False),
            "period": FieldSchema(selector=".period, .timeframe, .date-range", required=False),
            "target": FieldSchema(selector=".target, .goal, .benchmark", required=False),
            "category": FieldSchema(selector=".category, .type, .group", required=False),
        },
    },
    "competitive_intel": {
        "name": "Competitive Intelligence",
        "description": "Extract competitor data, pricing, and market intelligence",
        "common_selectors": [".competitor", ".comparison-row", "tr.product-row"],
        "fields": {
            "competitor_name": FieldSchema(selector=".name, .company, .brand, th", required=True),
            "product_name": FieldSchema(selector=".product, .product-name, h3", required=False),
            "price": FieldSchema(selector=".price, .cost, .pricing", required=False),
            "features": FieldSchema(selector=".features, .specs, .capabilities", required=False),
            "market_share": FieldSchema(
                selector=".market-share, .share, .percentage", required=False
            ),
            "rating": FieldSchema(selector=".rating, .score, .stars", required=False),
            "strengths": FieldSchema(selector=".strengths, .pros, .advantages", required=False),
            "weaknesses": FieldSchema(
                selector=".weaknesses, .cons, .disadvantages", required=False
            ),
            "website": FieldSchema(selector="a.website", attribute="href", required=False),
        },
    },
    "supply_chain": {
        "name": "Supply Chain/Inventory",
        "description": "Extract inventory, shipments, or supply chain data",
        "common_selectors": [".inventory-item", ".shipment", "tr.sku-row", ".product-row"],
        "fields": {
            "sku": FieldSchema(selector=".sku, .product-id, .item-number", required=True),
            "product_name": FieldSchema(
                selector=".name, .product-name, .description", required=True
            ),
            "quantity": FieldSchema(selector=".quantity, .qty, .stock", required=False),
            "unit_cost": FieldSchema(selector=".cost, .unit-cost, .price", required=False),
            "supplier": FieldSchema(selector=".supplier, .vendor, .manufacturer", required=False),
            "location": FieldSchema(selector=".location, .warehouse, .facility", required=False),
            "status": FieldSchema(selector=".status, .state, .availability", required=False),
            "lead_time": FieldSchema(selector=".lead-time, .delivery-time, .eta", required=False),
            "last_updated": FieldSchema(
                selector="time, .updated, .timestamp", attribute="datetime", required=False
            ),
        },
    },
    "sales_leads": {
        "name": "Sales Leads/Prospects",
        "description": "Extract sales leads, prospects, or customer data",
        "common_selectors": [".lead", ".prospect", ".contact", "tr.lead-row"],
        "fields": {
            "company_name": FieldSchema(
                selector=".company, .organization, .business-name", required=True
            ),
            "contact_name": FieldSchema(
                selector=".name, .contact-name, .full-name", required=False
            ),
            "title": FieldSchema(selector=".title, .position, .role", required=False),
            "email": FieldSchema(
                selector="a[href^='mailto:'], .email", attribute="href", required=False
            ),
            "phone": FieldSchema(selector=".phone, .tel, a[href^='tel:']", required=False),
            "industry": FieldSchema(selector=".industry, .sector, .vertical", required=False),
            "company_size": FieldSchema(selector=".size, .employees, .headcount", required=False),
            "revenue": FieldSchema(selector=".revenue, .annual-revenue", required=False),
            "location": FieldSchema(selector=".location, .city, .region", required=False),
            "lead_score": FieldSchema(selector=".score, .lead-score, .rating", required=False),
            "website": FieldSchema(selector="a.website", attribute="href", required=False),
        },
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
