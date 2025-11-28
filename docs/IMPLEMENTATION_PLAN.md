# Quarry Implementation Plan
## Portfolio Demonstration Enhancement

**Document Purpose**: Implementation handoff for coding agents  
**Project Goal**: Polish Quarry as a portfolio piece demonstrating full-stack expertise  
**Demo Context**: Embedded xterm on portfolio website (~2-3 minute walkthrough)

---

## Executive Summary

Quarry is a Python web data extraction CLI toolkit being positioned as a portfolio demonstration piece. The goal is to showcase expertise in building tools that "look great, function reliably, and simplify complex tasks" for potential clients and hiring managers.

**Target Audience**: Big tent - clients, hiring managers, developers, curious visitors  
**Demo URL**: https://news.ycombinator.com (Hacker News)

---

## Implementation Phases

### Phase 1: Database Sink Foundation
**Priority**: HIGH  
**Rationale**: Demonstrates real-world data engineering capability

#### Task 1.1: PostgreSQL Sink Implementation
- **Location**: `quarry/sinks/`
- **Model After**: Existing CSV/JSON/Parquet sinks in same directory
- **Requirements**:
  - Connection string configuration via CLI flags or environment variables
  - Table creation with appropriate schema inference from extracted data
  - Upsert capability for incremental extraction runs
  - Connection pooling for performance
  - Clear error messages for connection failures
- **Testing**: Add tests in `tests/test_ship.py` or new `tests/test_postgres_sink.py`

---

### Phase 2: UX Polish
**Priority**: HIGH  
**Rationale**: First impression matters for portfolio demos

#### Task 2.1: Color Scheme Overhaul
**Theme**: Mars/Jupiter Palette (warm, earthy, professional)

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Rusty Orange | `#CD4F39` | Primary accent, headers |
| Terracotta | `#E07A5F` | Secondary accent, highlights |
| Dusty Tan | `#D4A373` | Tertiary, borders |
| Warm Brown | `#8B5A2B` | Text emphasis |
| Muted Red | `#B85042` | Errors, warnings |

**Files to Modify**:
- `quarry/lib/display.py` - Primary Rich styling definitions
- `quarry/wizard.py` - Interactive prompt styling
- Any file using Rich `Console` with color definitions

**Implementation Notes**:
- Replace existing blue/cyan palette with Mars/Jupiter colors
- Maintain WCAG contrast ratios for accessibility
- Test in both light and dark terminal backgrounds

#### Task 2.2: Error Message Enhancement
**Goal**: Helpful, specific, actionable error messages

**Principles**:
1. State what went wrong clearly
2. Explain why it might have happened
3. Suggest specific remediation steps
4. Include relevant context (URLs, selectors, file paths)

**Priority Error Scenarios**:
- Network failures (connection refused, timeout, DNS resolution)
- Selector not found / no matches
- Invalid schema/job file syntax
- File permission errors
- Rate limiting detection

**Files to Modify**:
- `quarry/lib/http.py` - Network error handling
- `quarry/lib/selectors.py` - Selector matching errors
- `quarry/lib/schemas.py` - Schema validation errors
- CLI tool files - User-facing error presentation

#### Task 2.3: Dual-Mode UX Implementation
**Concept**: Two distinct entry points for different user needs

##### Mode 1: `quarry` (Free Exploration)
- Current behavior - power user mode
- All tools accessible directly
- Minimal hand-holding

##### Mode 2: `quarry foreman` (Guided Tutorial)
- New command group for guided experience
- Step-by-step walkthrough of the 5-tool pipeline
- Uses Hacker News as demo target
- Interactive prompts with explanations
- ~2-3 minute complete demo

**Implementation Location**: `quarry/foreman.py` (new file)

**Foreman Flow**:
```
1. Welcome message + project overview
2. Scout demo: "Let's discover what's on Hacker News..."
3. Survey demo: "Now let's analyze the page structure..."
4. Excavate demo: "Time to extract the data..."
5. Polish demo: "Let's clean and transform..."
6. Ship demo: "Finally, let's export to CSV..."
7. Summary + next steps
```

**Registration**: Add to `quarry/__main__.py` CLI group

---

### Phase 3: JavaScript Rendering Exploration
**Priority**: MEDIUM  
**Rationale**: Extends capability for modern web apps

#### Task 3.1: Evaluate JS Rendering Options
**Candidates to Evaluate**:
1. **Playwright** (preferred) - Modern, well-maintained, async
2. **Selenium** - Mature but heavier
3. **requests-html** - Lighter but less capable

**Evaluation Criteria**:
- Installation complexity
- Performance overhead
- Reliability across sites
- Docker compatibility (for xterm demo)

#### Task 3.2: Implementation (if proceeding)
- Add as optional dependency in `pyproject.toml`
- Graceful fallback when not installed
- CLI flag: `--render-js` or similar
- Integrate at HTTP layer in `quarry/lib/http.py`

**Scope Note**: This is exploratory. If integration proves complex, defer to future work.

---

### Phase 4: Deployment & Documentation
**Priority**: HIGH (for portfolio visibility)

#### Task 4.1: PyPI Publishing
**Requirements**:
- Clean up `pyproject.toml` metadata
- Ensure all dependencies properly declared
- Version bump to 1.0.0 (or appropriate)
- Create GitHub release workflow

**Files**: `pyproject.toml`, `.github/workflows/` (new)

#### Task 4.2: README Enhancement
**Current Location**: `README.md`

**Required Sections**:
- Hero section with project description
- Quick install: `pip install quarry`
- 30-second demo GIF or asciicast
- Feature highlights with icons
- Link to full documentation

**Quality Badges to Add**:
- PyPI version
- Python version support
- Test status (GitHub Actions)
- Code coverage (if available)
- License

#### Task 4.3: Git/Contribution Documentation
**Location**: `CONTRIBUTING.md` (existing, enhance)

**Required Content**:
- Development setup instructions
- Code style guide (reference ruff config)
- Testing instructions
- PR process
- Issue templates

#### Task 4.4: CLI Help Text Polish
**Scope**: Minimal - focus on `--help` output quality
- Clear, concise command descriptions
- Useful examples in help text
- Consistent formatting across all commands

---

## Out of Scope (Explicitly Deferred)

| Item | Reason |
|------|--------|
| Parallel extraction | Complexity vs. demo value |
| Plugin system | Over-engineering for portfolio |
| Web UI | Focus on CLI excellence |
| `quarry status` command | Nice-to-have, not essential |
| Architecture cleanup | Working code > perfect code |
| Connector abstraction refactor | Internal, not demo-visible |

---

## File Location Reference

### Core CLI Tools
- `quarry/tools/scout.py` - Discovery tool
- `quarry/tools/survey.py` - Analysis tool  
- `quarry/tools/excavate.py` - Extraction tool
- `quarry/tools/polish.py` - Transformation tool
- `quarry/tools/ship.py` - Export tool

### Library Code
- `quarry/lib/display.py` - Rich console styling ⭐ COLOR CHANGES
- `quarry/lib/http.py` - HTTP client ⭐ ERROR MESSAGES
- `quarry/lib/selectors.py` - CSS/XPath handling ⭐ ERROR MESSAGES
- `quarry/lib/schemas.py` - Schema validation ⭐ ERROR MESSAGES

### Sinks
- `quarry/sinks/csv.py` - CSV export
- `quarry/sinks/json.py` - JSON export
- `quarry/sinks/parquet.py` - Parquet export
- `quarry/sinks/postgres.py` - **NEW** PostgreSQL export

### Configuration
- `pyproject.toml` - Package metadata, dependencies
- `pytest.ini` - Test configuration
- `requirements.txt` - Production dependencies

---

## Validation Checklist

### Before Demo Launch
- [ ] All 5 CLI tools work end-to-end with Hacker News
- [ ] `quarry foreman` completes full guided demo without errors
- [ ] Color scheme applied consistently across all Rich output
- [ ] Error messages are helpful and non-technical
- [ ] PostgreSQL sink functional with local database
- [ ] `pip install quarry` works from PyPI
- [ ] README renders correctly on GitHub and PyPI
- [ ] All quality badges display correctly
- [ ] Demo runs smoothly in xterm environment
- [ ] No sensitive data or credentials in codebase

### Quality Gates
- [ ] `pytest` passes all tests
- [ ] `ruff check .` passes
- [ ] `ruff format .` produces no changes
- [ ] `mypy` passes (existing coverage)

---

## Implementation Notes for Agents

1. **Preserve existing functionality** - This is enhancement, not rewrite
2. **Test incrementally** - Run pytest after each significant change
3. **Commit atomically** - One logical change per commit
4. **Prioritize visibility** - Focus on what demo visitors will see
5. **When in doubt, simplify** - Impressive simplicity > complex features

---

## Success Metrics

The implementation is successful when:
1. A first-time visitor can run `quarry foreman` and understand the tool in 2-3 minutes
2. The terminal output looks polished and professional
3. Error messages guide users to solutions rather than confusion
4. The tool installs cleanly via pip
5. The GitHub repo looks maintained and professional (badges, docs, recent commits)

---

*Document generated for implementation agent handoff*  
*Last updated: Session refinement complete*
