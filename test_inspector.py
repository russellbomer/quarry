#!/usr/bin/env python3
"""Test the wizard HTML analysis on Hacker News."""

from scrapesuite.http import get_html
from scrapesuite.inspector import find_item_selector, inspect_html, preview_extraction

# Test URL
url = "https://news.ycombinator.com/"

print("Fetching HTML from Hacker News...")
html = get_html(url)

print("\n=== HTML Inspection ===")
analysis = inspect_html(html)
print(f"Title: {analysis['title']}")
print(f"Total links: {analysis['total_links']}")

print("\n=== Repeated Classes ===")
for cls_info in analysis['repeated_classes'][:5]:
    print(f"  .{cls_info['class']} - {cls_info['count']} items - {cls_info['sample_text'][:50]}")

print("\n=== Containers ===")
for container in analysis['containers'][:3]:
    print(f"  {container['tag']}.{container['class']} - {container['child_count']} children of {container['child_tag']}")

print("\n=== Item Selector Detection ===")
candidates = find_item_selector(html, min_items=3)
for i, candidate in enumerate(candidates[:5], 1):
    print(f"{i}. {candidate['selector']}")
    print(f"   Count: {candidate['count']}")
    print(f"   Sample: {candidate.get('sample_title', '')[:60]}")
    print(f"   URL: {candidate.get('sample_url', '')[:60]}")
    print()

# Test extraction with .athing (HN story rows)
print("\n=== Testing Extraction ===")
item_selector = ".athing"
print(f"Using selector: {item_selector}")

# Manual field selectors for HN
field_selectors = {
    "title": "span.titleline a",
    "url": "span.titleline a::attr(href)",
}

previews = preview_extraction(html, item_selector, field_selectors)

print(f"\nExtracted {len(previews)} items:")
for i, item in enumerate(previews, 1):
    print(f"\n{i}. {item.get('title', '')[:60]}")
    print(f"   URL: {item.get('url', '')[:60]}")

