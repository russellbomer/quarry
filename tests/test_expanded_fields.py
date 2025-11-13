"""Tests for expanded field type coverage."""

from quarry.framework_profiles import (
    DrupalViewsProfile,
    WordPressProfile,
    ShopifyProfile,
    DjangoAdminProfile,
    ReactComponentProfile,
)


def test_expanded_field_types_drupal():
    """Test that Drupal profile includes all new field types."""
    mappings = DrupalViewsProfile.get_field_mappings()
    
    # Original fields
    assert "title" in mappings
    assert "url" in mappings
    assert "date" in mappings
    assert "author" in mappings
    assert "body" in mappings
    assert "image" in mappings
    
    # New fields
    assert "published_date" in mappings
    assert "updated_date" in mappings
    assert "excerpt" in mappings
    assert "content" in mappings
    assert "thumbnail" in mappings
    assert "category" in mappings
    assert "tags" in mappings
    assert "rating" in mappings
    assert "location" in mappings
    assert "phone" in mappings
    assert "email" in mappings


def test_expanded_field_types_wordpress():
    """Test that WordPress profile includes expanded field types."""
    mappings = WordPressProfile.get_field_mappings()
    
    assert "published_date" in mappings
    assert "updated_date" in mappings
    assert "excerpt" in mappings
    assert "content" in mappings
    assert "thumbnail" in mappings
    assert "category" in mappings
    assert "tags" in mappings
    assert "rating" in mappings
    
    # WordPress-specific patterns
    assert ".published" in mappings["published_date"]
    assert ".updated" in mappings["updated_date"]
    assert ".entry-summary" in mappings["excerpt"]
    assert ".cat-links" in mappings["category"]
    assert ".tag-links" in mappings["tags"]


def test_shopify_ecommerce_fields():
    """Test that Shopify profile has e-commerce specific fields."""
    mappings = ShopifyProfile.get_field_mappings()
    
    # Core product fields
    assert "price" in mappings
    assert "title" in mappings
    assert "image" in mappings
    
    # Extended e-commerce fields
    assert "thumbnail" in mappings
    assert "category" in mappings
    assert "tags" in mappings
    assert "rating" in mappings
    assert "description" in mappings
    assert "vendor" in mappings
    
    # Shopify-specific patterns
    assert ".product-price" in mappings["price"]
    assert ".money" in mappings["price"]
    assert ".product-vendor" in mappings["vendor"]


def test_django_admin_timestamp_fields():
    """Test that Django Admin distinguishes published vs updated dates."""
    mappings = DjangoAdminProfile.get_field_mappings()
    
    assert "published_date" in mappings
    assert "updated_date" in mappings
    assert "category" in mappings
    assert "tags" in mappings
    assert "status" in mappings
    
    # Django-specific field names
    assert ".field-created" in mappings["published_date"]
    assert ".field-modified" in mappings["updated_date"]
    assert ".field-status" in mappings["status"]


def test_react_modern_field_patterns():
    """Test that React profile has PascalCase field patterns."""
    mappings = ReactComponentProfile.get_field_mappings()
    
    # Core fields
    assert "title" in mappings
    assert "date" in mappings
    assert "author" in mappings
    
    # Extended fields
    assert "published_date" in mappings
    assert "updated_date" in mappings
    assert "excerpt" in mappings
    assert "content" in mappings
    assert "thumbnail" in mappings
    assert "category" in mappings
    assert "tags" in mappings
    assert "rating" in mappings
    
    # PascalCase patterns
    assert "[class*='PublishedDate']" in mappings["published_date"]
    assert "[class*='UpdatedAt']" in mappings["updated_date"]
    assert "[class*='Excerpt']" in mappings["excerpt"]
    assert "[class*='Rating']" in mappings["rating"]


def test_field_type_distinctness():
    """Test that published_date and updated_date are distinct."""
    drupal = DrupalViewsProfile.get_field_mappings()
    
    # They should have different patterns
    assert drupal["published_date"] != drupal["updated_date"]
    
    # Published should focus on creation
    published_patterns = " ".join(drupal["published_date"])
    assert "created" in published_patterns or "published" in published_patterns
    
    # Updated should focus on modification
    updated_patterns = " ".join(drupal["updated_date"])
    assert "changed" in updated_patterns or "modified" in updated_patterns or "updated" in updated_patterns


def test_excerpt_vs_content_distinction():
    """Test that excerpt and content have different selectors."""
    wordpress = WordPressProfile.get_field_mappings()
    
    # Should be distinct
    assert wordpress["excerpt"] != wordpress["content"]
    
    # Excerpt should be summary-like
    assert ".entry-summary" in wordpress["excerpt"]
    
    # Content should be full content
    assert ".entry-content" in wordpress["content"]


def test_thumbnail_vs_image_patterns():
    """Test that thumbnail uses smaller image patterns."""
    shopify = ShopifyProfile.get_field_mappings()
    
    assert "thumbnail" in shopify
    assert "image" in shopify
    
    # Thumbnail patterns should reference thumb/thumbnail
    thumb_patterns = " ".join(shopify["thumbnail"])
    assert "thumbnail" in thumb_patterns.lower()


def test_category_and_tags_separate():
    """Test that category and tags are separate fields."""
    wordpress = WordPressProfile.get_field_mappings()
    
    assert "category" in wordpress
    assert "tags" in wordpress
    assert wordpress["category"] != wordpress["tags"]
    
    # Should have appropriate WordPress classes
    assert ".cat-links" in wordpress["category"]
    assert ".tag-links" in wordpress["tags"]


def test_all_profiles_have_core_fields():
    """Test that all profiles at least have title and url."""
    from quarry.framework_profiles import FRAMEWORK_PROFILES
    
    for profile_class in FRAMEWORK_PROFILES:
        mappings = profile_class.get_field_mappings()
        
        # Skip Tailwind which defers to generic detection
        if profile_class.name == "tailwind":
            continue
        
        # Every profile should have title
        assert "title" in mappings, f"{profile_class.name} missing title mapping"
        
        # Most should have url (except maybe some admin interfaces)
        if profile_class.name not in ["django_admin"]:
            assert "url" in mappings, f"{profile_class.name} missing url mapping"


def test_field_coverage_count():
    """Test that profiles have substantial field coverage."""
    drupal = DrupalViewsProfile.get_field_mappings()
    
    # Drupal should now have 17+ field types
    assert len(drupal) >= 17, f"Expected 17+ field types, got {len(drupal)}"
    
    wordpress = WordPressProfile.get_field_mappings()
    # WordPress should have 15+ field types
    assert len(wordpress) >= 15, f"Expected 15+ field types, got {len(wordpress)}"
    
    shopify = ShopifyProfile.get_field_mappings()
    # Shopify should have 10+ field types (e-commerce focused)
    assert len(shopify) >= 10, f"Expected 10+ field types, got {len(shopify)}"
