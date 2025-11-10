"""Debug script to see what the live FDA page structure looks like."""

from scrapesuite.http import get_html
from scrapesuite.inspector import find_item_selector
from bs4 import BeautifulSoup

url = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"

print("Fetching FDA page...")
html = get_html(url)

print("\nFinding item selectors...")
candidates = find_item_selector(html, min_items=3)

print(f"\nFound {len(candidates)} candidates\n")

# Show all candidates with more detail
for i, candidate in enumerate(candidates[:10], 1):
    print(f"{i}. {candidate['selector']} ({candidate['count']} items)")
    print(f"   Confidence: {candidate['confidence']}")
    print(f"   Sample: {candidate.get('sample_title', '')[:100]}")
    print(f"   URL: {candidate.get('sample_url', '')[:80]}")
    print()

# Let's also manually inspect the structure
print("\n" + "="*80)
print("Manual inspection - looking for recall items...")
print("="*80)

soup = BeautifulSoup(html, "html.parser")

# Look for the actual recall links
recall_links = []
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    if "recalls-market-withdrawals-safety-alerts" in href and href != url:
        text = a.get_text(strip=True)
        if text and len(text) > 10:  # Likely a title, not navigation
            recall_links.append({
                "text": text[:80],
                "href": href[:100],
                "classes": " ".join(a.get("class", [])),
                "parent_tag": a.parent.name,
                "parent_classes": " ".join(a.parent.get("class", [])),
            })

print(f"\nFound {len(recall_links)} recall links")
print("\nFirst 5 recall links:")
for i, link in enumerate(recall_links[:5], 1):
    print(f"\n{i}. {link['text']}")
    print(f"   Link classes: {link['classes']}")
    print(f"   Parent: <{link['parent_tag']} class='{link['parent_classes']}'>")
    print(f"   URL: {link['href']}")

# Find common parent structure
if recall_links:
    print("\n" + "="*80)
    print("Analyzing parent structure...")
    print("="*80)
    
    # Get first recall link element
    first_link = soup.find("a", href=lambda x: x and "recalls-market-withdrawals-safety-alerts" in x and x != url)
    
    if first_link:
        # Walk up the tree
        print("\nParent hierarchy (from link up):")
        current = first_link
        depth = 0
        while current and depth < 10:
            classes = " ".join(current.get("class", []))
            tag_info = f"<{current.name}>"
            if classes:
                tag_info += f" class='{classes}'"
            if current.get("id"):
                tag_info += f" id='{current.get('id')}'"
            
            print(f"  {'  ' * depth}{tag_info}")
            
            current = current.parent
            depth += 1
            if current and current.name in ["body", "html"]:
                break
