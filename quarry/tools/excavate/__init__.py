"""
Forge - Extraction Execution Engine

Executes schema-driven extraction at scale with:
- Schema-based HTML parsing
- Pagination support
- Rate limiting (via lib/http)
- JSONL output streaming
- Progress tracking
"""

from .executor import ForgeExecutor, write_jsonl, append_jsonl
from .parser import SchemaParser

__all__ = ["ForgeExecutor", "SchemaParser", "write_jsonl", "append_jsonl"]
