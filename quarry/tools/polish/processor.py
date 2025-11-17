"""Polish processor - orchestrates data transformation and enrichment."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from .deduplicator import Deduplicator
from .transformers import apply_transformation
from .validators import validate_record


class PolishProcessor:
    """
    Process JSONL data with transformations, deduplication, and validation.

    Implements streaming JSONL → JSONL transformation pipeline.
    """

    def __init__(self):
        """Initialize processor."""
        self.stats = {
            "records_read": 0,
            "records_written": 0,
            "records_skipped": 0,
            "duplicates_removed": 0,
            "validation_errors": 0,
        }

    def process(
        self,
        input_file: str | Path,
        output_file: str | Path,
        *,
        deduplicate: bool = False,
        dedupe_keys: list[str] | None = None,
        dedupe_strategy: Literal["first", "last"] = "first",
        transformations: dict[str, list[dict[str, Any]]] | None = None,
        validation_rules: dict[str, dict[str, Any]] | None = None,
        skip_invalid: bool = False,
        filter_func: Callable[[dict[str, Any]], bool] | None = None,
    ) -> dict[str, int]:
        """
        Process JSONL file with transformations and deduplication.

        Args:
            input_file: Input JSONL file path
            output_file: Output JSONL file path
            deduplicate: Whether to deduplicate records
            dedupe_keys: Fields to use for deduplication (None = full record)
            dedupe_strategy: "first" or "last"
            transformations: Field transformations to apply
                           Example: {"url": [{"transform": "extract_domain"}]}
            validation_rules: Validation rules per field
            skip_invalid: Skip records that fail validation
            filter_func: Optional filter function (return True to keep)

        Returns:
            Statistics dictionary
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        # Initialize deduplicator if needed
        deduplicator = None
        if deduplicate:
            deduplicator = Deduplicator(
                key_fields=dedupe_keys,
                strategy=dedupe_strategy,
            )

        # Process records
        records_to_write = []

        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    self.stats["records_read"] += 1

                    # Apply transformations
                    if transformations:
                        record = self._apply_transformations(record, transformations)

                    # Apply filter
                    if filter_func and not filter_func(record):
                        self.stats["records_skipped"] += 1
                        continue

                    # Validate
                    if validation_rules:
                        errors = validate_record(record, validation_rules)
                        if errors:
                            self.stats["validation_errors"] += 1
                            if skip_invalid:
                                self.stats["records_skipped"] += 1
                                continue

                    # Check for duplicates
                    if deduplicator:
                        if dedupe_strategy == "first":
                            if deduplicator.is_duplicate(record):
                                self.stats["duplicates_removed"] += 1
                                continue
                        else:
                            # For "last" strategy, collect all records
                            deduplicator.is_duplicate(record)

                    records_to_write.append(record)

                except json.JSONDecodeError:
                    self.stats["records_skipped"] += 1
                    continue

        # Handle "last" deduplication strategy
        if deduplicator and dedupe_strategy == "last":
            unique_records = deduplicator.get_unique_records()
            self.stats["duplicates_removed"] = self.stats["records_read"] - len(unique_records)
            records_to_write = unique_records

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            for record in records_to_write:
                f.write(json.dumps(record) + "\n")
                self.stats["records_written"] += 1

        return self.stats

    def _apply_transformations(
        self,
        record: dict[str, Any],
        transformations: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        """
        Apply transformations to record fields.

        Args:
            record: Input record
            transformations: Field transformation definitions

        Returns:
            Transformed record
        """
        for field, transforms in transformations.items():
            if field not in record:
                continue

            value = record[field]

            for transform_def in transforms:
                transform_name = transform_def.get("transform")
                if not transform_name:
                    continue

                # Get additional kwargs
                kwargs = {k: v for k, v in transform_def.items() if k != "transform"}

                try:
                    value = apply_transformation(value, transform_name, **kwargs)
                except Exception:
                    # Transformation failed, keep original value
                    pass

            record[field] = value

        return record
