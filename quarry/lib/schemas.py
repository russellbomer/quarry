"""Schema definitions for extraction blueprints."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class FieldSchema(BaseModel):
    """Schema for a single field in extraction."""
    
    selector: str = Field(..., description="CSS selector for the field")
    attribute: str | None = Field(None, description="HTML attribute to extract (e.g., 'href', 'src')")
    required: bool = Field(False, description="Whether this field is required")
    multiple: bool = Field(False, description="Whether to extract multiple matches")
    default: Any = Field(None, description="Default value if extraction fails")
    
    @field_validator("selector")
    @classmethod
    def validate_selector(cls, v: str) -> str:
        """Validate selector is not empty."""
        if not v or not v.strip():
            raise ValueError("Selector cannot be empty")
        return v.strip()


class PaginationSchema(BaseModel):
    """Schema for pagination handling."""
    
    next_selector: str = Field(..., description="Selector for next page link")
    max_pages: int | None = Field(None, description="Maximum pages to scrape")
    wait_seconds: float = Field(1.0, description="Seconds to wait between pages")


class ExtractionSchema(BaseModel):
    """Complete schema for web data extraction."""
    
    name: str = Field(..., description="Schema name/identifier")
    description: str | None = Field(None, description="Optional description")
    version: int = Field(1, description="Schema version")
    
    # Core extraction config
    url: str | None = Field(None, description="Target URL (optional, can be provided at runtime)")
    item_selector: str = Field(..., description="CSS selector for item containers")
    fields: dict[str, FieldSchema] = Field(..., description="Field extraction definitions")
    
    # Optional features
    pagination: PaginationSchema | None = Field(None, description="Pagination configuration")
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("Schema name cannot be empty")
        return v.strip()
    
    @field_validator("item_selector")
    @classmethod
    def validate_item_selector(cls, v: str) -> str:
        """Validate item selector is not empty."""
        if not v or not v.strip():
            raise ValueError("Item selector cannot be empty")
        return v.strip()
    
    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: dict[str, FieldSchema]) -> dict[str, FieldSchema]:
        """Validate at least one field exists."""
        if not v:
            raise ValueError("At least one field must be defined")
        return v


def load_schema(path: str | Path) -> ExtractionSchema:
    """
    Load and validate extraction schema from YAML file.
    
    Args:
        path: Path to schema YAML file
    
    Returns:
        Validated ExtractionSchema
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If YAML is invalid or schema validation fails
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML: {e}") from e
    
    if not data:
        raise ValueError("Schema file is empty")
    
    # Parse and validate with Pydantic
    try:
        return ExtractionSchema(**data)
    except Exception as e:
        raise ValueError(f"Schema validation failed: {e}") from e


def save_schema(schema: ExtractionSchema, path: str | Path) -> None:
    """
    Save extraction schema to YAML file.
    
    Args:
        schema: ExtractionSchema to save
        path: Output path for YAML file
    """
    path = Path(path)
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict and write YAML
    data = schema.model_dump(exclude_none=True)
    
    with path.open("w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )


def validate_schema_dict(data: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a schema dictionary without raising exceptions.
    
    Args:
        data: Dictionary to validate as schema
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ExtractionSchema(**data)
        return True, ""
    except Exception as e:
        return False, str(e)
