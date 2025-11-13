"""
Probe - HTML Analysis Tool

Analyzes web pages to detect:
- Frameworks and patterns (Bootstrap, React, WordPress, etc.)
- Repeated elements (likely data items)
- Page structure and metadata
- Extraction suggestions
"""

from .analyzer import analyze_page

__all__ = ["analyze_page"]
