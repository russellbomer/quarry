"""Parquet sink implementation."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

from quarry.transforms.base import Frame


class ParquetSink:
    """Parquet file sink with timezone-aware timestamp paths."""

    def __init__(self, path_template: str, timezone: str = "America/New_York"):
        self.path_template = path_template
        self.timezone = timezone

    def write(self, df: Frame, job: str) -> str:
        """Write DataFrame to Parquet file."""
        if df.empty:
            raise ValueError("Cannot write empty DataFrame")

        # Expand path template with timezone-aware timestamp
        try:
            tz = ZoneInfo(self.timezone)
        except Exception:
            tz = ZoneInfo("America/New_York")  # Fallback

        now = datetime.now(tz)
        path_str = now.strftime(self.path_template)

        # Replace {job} placeholder if present
        path_str = path_str.replace("{job}", job)

        output_path = Path(path_str)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, output_path)

        return str(output_path)
