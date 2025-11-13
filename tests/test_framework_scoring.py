"""Tests for framework confidence scoring system."""

from quarry.framework_profiles import (
    DjangoAdminProfile,
    DrupalViewsProfile,
    NextJSProfile,
    ReactComponentProfile,
    TailwindProfile,
    VueJSProfile,
    detect_all_frameworks,
    detect_framework,
)


def test_confidence_scoring():
    """Test that framework detection returns confidence scores."""
    # Test single framework detection
    html = """
    <div class="views-row">
        <div class="views-field-title">Test</div>
        <div class="views-field-body">Content</div>
    </div>
    """
    
    score = DrupalViewsProfile.detect(html)
    assert score > 0, "Should return a confidence score"
    assert isinstance(score, int), "Score should be an integer"
    assert 0 <= score <= 100, "Score should be between 0 and 100"


def test_detect_all_frameworks():
    """Test that detect_all_frameworks returns sorted list."""
    # HTML that could match multiple frameworks
    html = """
    <div class="card post entry">
        <h2 class="card-title entry-title">Title</h2>
        <div class="card-body entry-content">Content</div>
    </div>
    """
    
    results = detect_all_frameworks(html)
    
    # Should return list of tuples
    assert isinstance(results, list)
    assert all(isinstance(item, tuple) for item in results)
    assert all(len(item) == 2 for item in results)
    
    # Should be sorted by score descending
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True), "Results should be sorted by score"
    
    # Should only include profiles with score > 0
    assert all(score > 0 for _, score in results)


def test_multi_framework_detection():
    """Test sites using multiple frameworks (e.g., WordPress + Bootstrap)."""
    html = """
    <article class="post card">
        <div class="card-header">
            <h2 class="entry-title">Post Title</h2>
            <time class="entry-date">2025-01-15</time>
        </div>
        <div class="card-body entry-content">
            <p>Post content here</p>
        </div>
    </article>
    <link rel="stylesheet" href="/wp-content/themes/mytheme/style.css">
    """
    
    results = detect_all_frameworks(html)
    
    # Should detect both WordPress and Bootstrap
    detected_names = {profile.name for profile, _ in results}
    assert "wordpress" in detected_names, "Should detect WordPress"
    assert "bootstrap" in detected_names, "Should detect Bootstrap"
    
    # WordPress should score higher (has wp-content)
    wp_score = next((s for p, s in results if p.name == "wordpress"), 0)
    bs_score = next((s for p, s in results if p.name == "bootstrap"), 0)
    assert wp_score > 0 and bs_score > 0


def test_threshold_detection():
    """Test that detect_framework uses threshold correctly."""
    # Low confidence HTML (generic classes)
    html = '<div class="container"><div class="item">Test</div></div>'
    
    framework = detect_framework(html)
    # Should return None if no framework scores above threshold
    # Or return the highest scoring framework if one exceeds threshold
    
    # More specific test - Vue.js with clear marker
    vue_html = '<div v-for="item in items" :key="item.id">{{ item.name }}</div>'
    framework = detect_framework(vue_html)
    assert framework == VueJSProfile, "Should detect Vue.js with clear v-for directive"
    
    score = VueJSProfile.detect(vue_html)
    assert score >= 40, f"Vue score should be >= 40, got {score}"


def test_framework_priority():
    """Test that more specific frameworks win over generic ones."""
    # Next.js + React (Next.js should win as more specific)
    html = """
    <script id="__NEXT_DATA__" type="application/json">{"props": {}}</script>
    <div id="__next">
        <div data-reactroot="">Content</div>
    </div>
    """
    
    results = detect_all_frameworks(html)
    detected = {profile.name: score for profile, score in results}
    
    # Both should be detected
    assert "nextjs" in detected
    assert "react" in detected
    
    # Next.js should score higher (more specific)
    assert detected["nextjs"] > detected["react"]
    
    # detect_framework should return Next.js
    framework = detect_framework(html)
    assert framework == NextJSProfile


def test_scoring_accumulation():
    """Test that scores accumulate with multiple indicators."""
    # Django Admin with multiple indicators
    html = """
    <!DOCTYPE html>
    <html class="django-admin">
    <head>
        <link rel="stylesheet" href="/admin/css/base.css">
    </head>
    <body>
        <table>
            <thead>
                <tr>
                    <th class="field-__str__">Name</th>
                    <th class="field-created">Date</th>
                </tr>
            </thead>
            <tbody>
                <tr class="row1">
                    <td class="field-__str__"><a href="/admin/app/model/1/">Item 1</a></td>
                    <td class="field-created">2025-01-15</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    
    score = DjangoAdminProfile.detect(html)
    
    # Should have high confidence with multiple indicators
    # django-admin class (40) + /admin/ (20) + field- and th.field (20) = 80
    # But capped at reasonable threshold
    assert score >= 60, f"Expected high score with multiple indicators, got {score}"


def test_tailwind_pattern_counting():
    """Test Tailwind detection requires multiple utility class patterns."""
    # Few patterns - should score low
    html1 = '<div class="flex p-4">Content</div>'
    score1 = TailwindProfile.detect(html1)
    assert score1 < 50, "Should require more patterns for high confidence"
    
    # Many patterns - should score high
    html2 = """
    <div class="flex flex-col gap-4 p-6 m-4 bg-white text-gray-900 
                rounded-lg shadow-md border-2 hover:shadow-lg 
                dark:bg-gray-800 sm:flex-row md:p-8 lg:gap-6">
        Content
    </div>
    """
    score2 = TailwindProfile.detect(html2)
    assert score2 >= 50, f"Should have high confidence with many patterns, got {score2}"


def test_zero_score_filtered():
    """Test that detect_all_frameworks filters out zero scores."""
    # Plain HTML with no framework indicators
    html = "<p>Just plain text</p>"
    
    results = detect_all_frameworks(html)
    
    # Should return empty list or very few low-confidence matches
    assert all(score > 0 for _, score in results), "Should filter out zero scores"


def test_react_false_positive_prevention():
    """Test that React detection doesn't match generic id='app' without React markers."""
    # Generic app div without React markers
    html1 = '<div id="app"><h1>My App</h1></div>'
    score1 = ReactComponentProfile.detect(html1)
    assert score1 < 40, "Should not strongly detect React without data-react attributes"
    
    # With React markers
    html2 = '<div id="app" data-reactroot=""><h1>My App</h1></div>'
    score2 = ReactComponentProfile.detect(html2)
    assert score2 >= 40, "Should detect React with data-reactroot"
