"""
Example: Using the selector utilities to handle dynamic CSS

This script demonstrates:
1. Validating selectors before deploying schemas
2. Building robust selectors that avoid dynamic classes
3. Creating fallback chains for resilience
4. Detecting frameworks to inform strategy
"""

import sys
from pathlib import Path

# Add quarry to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from bs4 import BeautifulSoup

from quarry.framework_profiles import detect_framework, suggest_extraction_strategy
from quarry.lib.selectors import (
    build_fallback_chain,
    build_robust_selector,
    validate_selector,
)


def example_validate_selectors():
    """Example: Validate selectors before using them in a schema"""
    print("\n=== EXAMPLE 1: Validate Selectors ===\n")

    # Fetch sample HTML
    url = "https://www.nytimes.com/section/us"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # Test different selectors
    selectors_to_test = [
        "h3.css-17p10p8 a",  # Brittle - uses dynamic class
        "h3 a",  # Robust - structural
        "article h3 a",  # More specific structural
        ".title",  # Generic class
    ]

    for selector in selectors_to_test:
        result = validate_selector(soup, selector)
        print(f"Selector: {selector:30} Valid: {result['valid']:5} Count: {result['count']}")
        if not result['valid']:
            print(f"  Warning: {result['warnings']}")

    print("\n✓ Recommendation: Use 'h3 a' or 'article h3 a' for NYT")


def example_build_robust_selector():
    """Example: Convert brittle selectors to robust ones"""
    print("\n=== EXAMPLE 2: Build Robust Selectors ===\n")

    # Brittle selectors from user schemas
    brittle_selectors = [
        ("h3.css-17p10p8.emotion-abc123 a", ["class"]),
        ("div#app > div.css-xyz > article.css-123", ["class"]),
        ("span[data-test-id='author-1234']", ["id"]),
    ]

    for selector, context in brittle_selectors:
        robust = build_robust_selector(selector, context)
        print(f"Brittle:  {selector}")
        print(f"Robust:   {robust}")
        print()


def example_fallback_chain():
    """Example: Create fallback chains for resilience"""
    print("\n=== EXAMPLE 3: Fallback Chains ===\n")

    # Build chain for title extraction
    chain = build_fallback_chain(
        "h3.css-17p10p8 a",  # Current working selector
        ["class", "tag"],  # Available context
    )

    print("Title extraction fallback chain:")
    for i, selector in enumerate(chain.selectors, 1):
        print(f"  {i}. {selector}")

    # Simulate extraction
    url = "https://www.nytimes.com/section/us"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try chain
    value = chain.extract(soup)
    preview = value[:50] if value else ""
    tier = chain.selectors.index(value[1]) + 1 if value else "N/A"
    print(f"\n✓ Extracted: '{preview}...' using selector tier {tier}")


def example_framework_detection():
    """Example: Detect framework and get extraction strategy"""
    print("\n=== EXAMPLE 4: Framework Detection ===\n")

    # Fetch NYT HTML
    url = "https://www.nytimes.com/section/us"
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # Detect framework
    framework = detect_framework(html, soup, url)
    print(f"Detected Framework: {framework.name}")
    print(f"Confidence: {framework.confidence:.0%}")
    print(f"Indicators: {', '.join(framework.indicators)}")

    # Get extraction strategy
    strategy = suggest_extraction_strategy(soup, url)
    print(f"\n{strategy}")


def example_real_world_workflow():
    """Example: Complete workflow for handling a new site"""
    print("\n=== EXAMPLE 5: Real-World Workflow ===\n")

    url = "https://www.nytimes.com/section/us"
    print(f"Target: {url}")

    # Step 1: Fetch HTML
    print("\n1. Fetching HTML...")
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    print("   ✓ HTML fetched")

    # Step 2: Detect framework
    print("\n2. Detecting framework...")
    framework = detect_framework(html, soup, url)
    print(f"   ✓ Framework: {framework.name} ({framework.confidence:.0%})")

    # Step 3: Get strategy
    print("\n3. Getting extraction strategy...")
    strategy = suggest_extraction_strategy(soup, url)
    print(f"   ✓ Strategy: {strategy.split(':')[0]}")

    # Step 4: Build selectors
    print("\n4. Building selectors...")

    # Find article containers
    articles = soup.select('article')
    print(f"   Found {len(articles)} articles")

    if articles:
        # Analyze first article
        first_article = articles[0]

        # Title
        title_element = first_article.select_one('h3 a')
        if title_element:
            title_selector = build_robust_selector('h3 a', ['tag'])
            print(f"   Title: {title_selector}")

        # URL
        url_element = first_article.select_one('a')
        if url_element:
            print("   URL: a::attr(href)")

        # Description
        desc_element = first_article.select_one('p')
        if desc_element:
            desc_selector = build_robust_selector('p', ['tag'])
            print(f"   Description: {desc_selector}")

    # Step 5: Validate selectors
    print("\n5. Validating selectors...")
    test_selectors = ['h3 a', 'a', 'p']
    for sel in test_selectors:
        result = validate_selector(soup, sel)
        print(f"   {sel:10} → {result['count']} matches")

    print("\n✓ Workflow complete! Ready to create schema.")


if __name__ == "__main__":
    print("=" * 70)
    print("SELECTOR UTILITIES EXAMPLES")
    print("=" * 70)

    # Run examples
    try:
        example_validate_selectors()
        example_build_robust_selector()
        example_fallback_chain()
        example_framework_detection()
        example_real_world_workflow()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
