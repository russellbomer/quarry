"""
Excavate - Extraction Execution Engine

Executes schema-driven extraction at scale with:
- Schema-based HTML parsing
- Pagination support
- Rate limiting (via lib/http)
- JSONL output streaming
- Progress tracking
"""

from .executor import ExcavateExecutor, append_jsonl, write_jsonl
from .parser import SchemaParser

__all__ = ["ExcavateExecutor", "SchemaParser", "append_jsonl", "write_jsonl"]
