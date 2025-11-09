"""Generic transform for selector-based extraction."""

from typing import Any

import pandas as pd


def normalize(records: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Generic normalization - just convert to DataFrame.
    
    For GenericConnector, the connector already extracts clean fields,
    so we just need to ensure DataFrame conversion.
    
    Args:
        records: List of records from GenericConnector
    
    Returns:
        Normalized DataFrame
    """
    if not records:
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    
    # Ensure required columns exist
    if "id" not in df.columns:
        df["id"] = df.get("url", pd.Series(range(len(df))).astype(str))
    
    if "url" not in df.columns:
        df["url"] = ""
    
    if "title" not in df.columns:
        df["title"] = ""
    
    # Clean up any empty strings
    df = df.fillna("")
    
    return df
