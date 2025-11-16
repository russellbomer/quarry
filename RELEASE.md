# Quarry Release Checklist

This document describes the steps for cutting a new Quarry release.

## 1. Pre-flight Checks

1. Ensure your working tree is clean (or only has intentional changes):

   ```bash
   git status
   ```

2. Run the full test suite:

   ```bash
   python -m pytest -q
   ```

3. Run formatters and linters:

   ```bash
   python -m ruff format .
   python -m ruff check .
   ```

4. (Optional but recommended) Run mypy over the `quarry` package:

   ```bash
   python -m mypy quarry
   ```

## 2. Bump Version

1. Decide on the new version using semantic versioning (e.g. `2.0.1`, `2.1.0`).
2. Update the version in `pyproject.toml` under `[project]`:

   ```toml
   [project]
   name = "quarry"
   version = "X.Y.Z"  # update this
   ```

3. Commit the version bump with a clear message, e.g. `chore: bump version to X.Y.Z`.

## 3. Build Artifacts

1. Create a fresh build (wheel + sdist):

   ```bash
   python -m build
   ```

   This should produce files under `dist/`.

2. (Optional) Inspect the wheel/metadata with tools like `twine` or `pip install dist/*.whl` in a temporary virtualenv.

## 4. Smoke Test from Built Package

1. Create a new virtual environment and install the built package:

   ```bash
   python -m venv .venv-release-test
   source .venv-release-test/bin/activate
   pip install dist/quarry-*.whl
   ```

2. Run a basic smoke test:

   ```bash
   quarry --help
   quarry scout https://example.com --help
   ```

3. Optionally, run a simple end-to-end pipeline with a local HTML file or a known-safe URL.

## 5. Publish

If you are publishing to PyPI:

1. Ensure you have `twine` installed:

   ```bash
   pip install twine
   ```

2. Upload the artifacts:

   ```bash
   twine upload dist/*
   ```

3. Tag the release in git:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

## 6. Post-Release

1. Update any badges or documentation (e.g., version badges) if needed.
2. Optionally, open a new `NEXT` section in your changelog or project board to track future work.

This checklist is intentionally minimal; adjust as needed for your CI/CD setup or organizational policies.
