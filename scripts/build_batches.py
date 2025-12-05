"""Batch builder: run all jobs and create timestamped Parquet chunks with index."""

import json
from pathlib import Path

from quarry.core import load_yaml, run_job
from quarry.lib import paths
from quarry.sinks.parquet import ParquetSink


def main() -> None:
    """Run all jobs and build batches."""
    jobs_dir = Path("jobs")
    if not jobs_dir.exists():
        print("ERROR: jobs/ directory not found")
        return

    yaml_files = sorted(jobs_dir.glob("*.yml"))
    if not yaml_files:
        print("No job YAML files found")
        return

    index: dict[str, list[str]] = {}

    for yaml_file in yaml_files:
        try:
            job_dict = load_yaml(str(yaml_file))
            job_name = job_dict["job"]

            # Run job offline
            df, _ = run_job(job_dict, max_items=200, offline=True)

            if df.empty:
                print(f"{job_name}: No data")
                continue

            # Write to timestamped Parquet
            job_cache_dir = paths.get_cache_dir(create=True) / job_name
            sink_path_template = str(job_cache_dir / "%Y%m%dT%H%M%SZ.parquet")
            sink = ParquetSink(sink_path_template)
            written_path = sink.write(df, job=job_name)

            # Update index
            if job_name not in index:
                index[job_name] = []
            index[job_name].append(written_path)

            print(f"{job_name}: {len(df)} rows -> {written_path}")

        except Exception as e:
            print(f"ERROR in {yaml_file}: {e}")
            continue

    # Write index.json
    index_path = paths.get_cache_dir(create=True) / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, sort_keys=True)

    print(f"Index written to {index_path}")


if __name__ == "__main__":
    main()
