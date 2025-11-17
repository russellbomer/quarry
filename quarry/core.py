"""Core job loading and execution logic."""

import warnings
from typing import Any

import pandas as pd
import yaml

from quarry.connectors import custom as custom_conn
from quarry.connectors import fda, generic, nws
from quarry.lib import http
from quarry.lib.policy import is_allowed_domain
from quarry.lib.ratelimit import DomainRateLimiter
from quarry.sinks.base import Sink
from quarry.sinks.csv import CSVSink
from quarry.sinks.jsonl import JSONLSink
from quarry.sinks.parquet import ParquetSink
from quarry.state import load_cursor, save_cursor, upsert_items
from quarry.transforms import custom as custom_tx
from quarry.transforms import fda as fda_transforms
from quarry.transforms import generic as generic_transforms
from quarry.transforms import nws as nws_transforms

# Registry of available connectors. Use broad type to allow varying constructors.
_CONNECTOR_REGISTRY: dict[str, Any] = {
    "custom_list": custom_conn.CustomConnector,
    "fda_list": fda.FDAConnector,
    "nws_list": nws.NWSConnector,
    "generic": generic.GenericConnector,
}

_TRANSFORM_REGISTRY: dict[str, Any] = {
    "custom": custom_tx.normalize,
    "fda_recalls": fda_transforms.normalize,
    "nws_alerts": nws_transforms.normalize,
    "generic": generic_transforms.normalize,
}


def _resolve_connector(
    source: dict[str, Any], policy: dict[str, Any], offline: bool, config: dict[str, Any]
):
    """Resolve and instantiate connector from source spec.

    Separated out to reduce complexity in run_job.
    """
    parser_name = source["parser"]
    connector_class = _CONNECTOR_REGISTRY[parser_name]
    entry_url = source.get("entry", "")
    allowlist = policy.get("allowlist", [])
    rate_limit_rps = source.get("rate_limit_rps", 1.0)

    # Enforce allowlist for live mode
    if not offline:
        if allowlist and not is_allowed_domain(entry_url, allowlist):
            raise ValueError(
                f"Domain not in allowlist for live mode: {entry_url}. Allowlist: {allowlist}"
            )

    return connector_class(
        entry_url=entry_url,
        allowlist=allowlist,
        rate_limit_rps=rate_limit_rps,
        config=config,
    )


def _apply_transform_pipeline(records: list[dict[str, Any]], transform: dict[str, Any]):
    """Apply transform pipeline to raw records and return a DataFrame.

    Separated to reduce branching in run_job.
    """
    df = pd.DataFrame(records)
    if df.empty:
        return df

    pipeline = transform.get("pipeline", [])
    for step in pipeline:
        if "normalize" in step:
            normalize_func = _TRANSFORM_REGISTRY.get(step["normalize"])
            if not normalize_func:
                available = ", ".join(_TRANSFORM_REGISTRY.keys())
                raise ValueError(
                    f"Unknown normalize function '{step['normalize']}'. Available: {available}"
                )
            df = normalize_func(records)

    return df


def _create_sink(sink_spec: dict[str, Any], timezone: str, job_name: str) -> Sink:
    """Create configured sink instance from spec.

    Separated to reduce run_job size.
    """
    sink_kind = sink_spec.get("kind", "parquet")
    sink_path_template = sink_spec.get("path", "data/cache/{job}/%Y%m%dT%H%M%SZ.parquet")
    if sink_kind == "parquet":
        sink: Sink = ParquetSink(sink_path_template, timezone=timezone)
    elif sink_kind == "csv":
        sink = CSVSink(sink_path_template, timezone=timezone)
    elif sink_kind == "jsonl":
        sink = JSONLSink(sink_path_template, timezone=timezone)
    else:
        available = "parquet, csv, jsonl"
        raise ValueError(f"Unknown sink kind '{sink_kind}'. Available: {available}")

    return sink


def load_yaml(path: str) -> dict[str, Any]:
    """Load and validate minimal YAML job spec schema."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as err:
        raise FileNotFoundError(f"Job file not found: {path}") from err
    except yaml.YAMLError as err:
        raise ValueError(f"Invalid YAML in {path}: {err}") from err

    if not isinstance(data, dict):
        raise ValueError(f"Job spec must be a dictionary: {path}")

    required_keys = ["version", "job", "source", "transform", "sink"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key '{key}' in job spec: {path}")

    if not isinstance(data["source"], dict) or "parser" not in data["source"]:
        raise ValueError(f"Invalid source.parser in job spec: {path}")

    if data["source"]["parser"] not in _CONNECTOR_REGISTRY:
        available = ", ".join(_CONNECTOR_REGISTRY.keys())
        raise ValueError(
            f"Unknown parser '{data['source']['parser']}' in {path}. Available: {available}"
        )

    return data


def run_job(
    job_dict: dict[str, Any],
    *,
    max_items: int = 200,
    offline: bool = True,
    db_path: str | None = None,
    timezone: str = "America/New_York",
) -> tuple[pd.DataFrame, str | None]:
    """
    Execute a job: collect, transform, dedupe, write.

    Returns:
        (dataframe, next_cursor)
    """
    job_name = job_dict["job"]
    source = job_dict["source"]
    transform = job_dict["transform"]
    sink_spec = job_dict["sink"]
    policy = job_dict.get("policy", {})

    # Configure per-domain rate limiting
    default_rps = policy.get("default_rps", 1.0)
    rate_limits = policy.get("rate_limits", {})
    if not offline and rate_limits:
        # Set up global rate limiter with custom limits
        limiter = DomainRateLimiter(default_rps=default_rps, rate_limits=rate_limits)
        http.set_rate_limiter(limiter)

    # Load cursor from state
    cursor = load_cursor(job_name, db_path=db_path)

    # Instantiate connector with config from YAML
    connector = _resolve_connector(source, policy, offline, job_dict)

    # Collect records
    detail_parser_name = source.get("detail_parser")
    records, next_cursor = connector.collect(
        cursor=cursor,
        max_items=max_items,
        offline=offline,
    )

    # Apply detail parser if specified (live mode only, or offline with fixture)
    if detail_parser_name and records:
        if hasattr(connector, "enrich_with_detail"):
            try:
                records = connector.enrich_with_detail(records, detail_parser_name, offline=offline)
            except FileNotFoundError:
                # Option C: skip if fixture missing in offline mode
                if offline:
                    warnings.warn(
                        f"Detail parser '{detail_parser_name}' specified but "
                        f"fixture not found. Continuing without detail data.",
                        stacklevel=2,
                    )

    # Apply transform pipeline
    df = _apply_transform_pipeline(records, transform)
    if df.empty:
        return df, cursor

    # Upsert to state (idempotent deduplication)
    upsert_items(job_name, records, db_path=db_path)

    # Save cursor
    if next_cursor:
        save_cursor(job_name, next_cursor, db_path=db_path)

    # Write sink
    sink = _create_sink(sink_spec, timezone, job_name)
    sink.write(df, job=job_name)

    return df, next_cursor
