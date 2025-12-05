# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

_No changes yet._

## [2.0.5] - 2025-12-05

### Added
- Introduced the `QUARRY_OUTPUT_DIR` environment variable and centralized path helper so every
  CLI, wizard flow, and tutorial can share a single output root.
- Added automated path selection for Scout, Survey, Excavate, Polish, and Ship when the
  environment variable is present, including new documentation and examples.
- Added regression coverage (`tests/test_paths.py`) to ensure the helper respects the
  configured base directory.

### Changed
- Wizard, Foreman, and sink internals now create deterministic schema/output/cache/exports
  under the resolved base directory, preventing scattered artifacts.
- Updated README and Usage Guide with configuration guidance and PowerShell examples.

### Fixed
- Ensured state and robots cache databases, sink templates, and batch scripts all
  pre-create directories within the configured output root to avoid collisions or missing
  folders on fresh installations.
