"""Generate job YAML files from schemas."""

from pathlib import Path
from typing import Optional
import yaml

from quarry.lib.schemas import ExtractionSchema


def generate_job_yaml(
    schema: ExtractionSchema,
    job_name: str,
    output_path: str = "data/cache/%Y%m%dT%H%M%SZ.parquet",
    sink_kind: str = "parquet",
    rate_limit: float = 1.0,
    cursor_field: str = "url",
    allowlist: Optional[list[str]] = None,
    max_items: Optional[int] = None,
) -> dict:
    """
    Generate a job YAML spec from an ExtractionSchema.
    
    Args:
        schema: ExtractionSchema object
        job_name: Name for the job
        output_path: Output file path template
        sink_kind: Output format (parquet, csv, jsonl)
        rate_limit: Requests per second
        cursor_field: Field to use for deduplication
        allowlist: Allowed domains
        max_items: Max items to extract (for testing)
    
    Returns:
        Dictionary representing the job YAML structure
    """
    # Build selectors dict from schema
    selectors = {
        "item": schema.item_selector,
        "fields": {}
    }
    
    # schema.fields is a dict[str, FieldSchema], so iterate over items
    for field_name, field_schema in schema.fields.items():
        if field_schema.attribute:
            # Attribute extraction syntax: selector::attr(name)
            selectors["fields"][field_name] = f"{field_schema.selector}::attr({field_schema.attribute})"
        else:
            selectors["fields"][field_name] = field_schema.selector
    
    # Build job spec
    job_spec = {
        "version": "1",
        "job": job_name,
        "source": {
            "kind": "html",
            "entry": schema.url or "https://example.com",
            "parser": "generic",  # Use generic parser with selectors
            "rate_limit_rps": rate_limit,
            "cursor": {
                "field": cursor_field,
                "stop_when_seen": True
            }
        },
        "selectors": selectors,
        "transform": {
            "pipeline": [
                {"normalize": "generic"}
            ]
        },
        "sink": {
            "kind": sink_kind,
            "path": output_path
        },
        "policy": {
            "robots": "allow",
            "allowlist": allowlist or []
        }
    }
    
    # Add pagination if schema has it
    if schema.pagination and schema.pagination.next_selector:
        job_spec["source"]["pagination"] = {
            "next_selector": schema.pagination.next_selector,
            "max_pages": schema.pagination.max_pages or 10
        }
    
    # Add max_items if specified
    if max_items:
        job_spec["max_items"] = max_items
    
    return job_spec


def save_job_yaml(job_spec: dict, output_file: str) -> None:
    """
    Save job spec to YAML file.
    
    Args:
        job_spec: Job specification dictionary
        output_file: Path to save YAML file
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(job_spec, f, default_flow_style=False, sort_keys=False)
