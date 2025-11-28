# Deploy & Operate

This guide shows how to build and run Quarry in production.

## Prerequisites
- Docker 24+
- Access to GitHub Container Registry (GHCR) if pulling published images

## Build locally
```bash
docker build -t ghcr.io/<owner>/quarry:local .
```

## Run CLI tools
```bash
# Show top-level CLI
docker run --rm ghcr.io/<owner>/quarry:local quarry --help

# Excavate with a schema from a bind mount
docker run --rm -v "$PWD:/work" -w /work \
  -e QUARRY_LOG_LEVEL=INFO \
  ghcr.io/<owner>/quarry:local quarry.excavate schemas/example.yml -o out.jsonl
```

## Configuration (env vars)
- `QUARRY_INTERACTIVE` (default `0`): prompt before bypassing robots blocks
- `QUARRY_IGNORE_ROBOTS` (default unset): set `1` to ignore robots (testing only)
- `QUARRY_LOG_LEVEL` (default `INFO`): Python logging level

## Pull from GHCR (after tagged release)
```bash
docker pull ghcr.io/<owner>/<repo>:latest
```

## CI/CD
- CI runs ruff, mypy (package only), pytest, and builds a wheel.
- Pushing a tag like `v2.0.1` triggers `release.yml`, building and pushing an image:
  - `ghcr.io/<owner>/<repo>:2.0.1`
  - `ghcr.io/<owner>/<repo>:latest`

## Notes
- Respect robots.txt for production usage.
- Consider proxy configuration and backoff tuning for high-volume runs.
