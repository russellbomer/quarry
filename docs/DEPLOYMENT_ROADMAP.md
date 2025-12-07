# Quarry v2.0 - Deployment Roadmap

**Status**: Pre-deployment preparation  
**Target**: Production-ready release  
**Current Branch**: `refactor-to-quarry`

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Critical Path Items](#critical-path-items)
3. [Testing & Validation](#testing--validation)
4. [Feature Completion](#feature-completion)
5. [Documentation & UX](#documentation--ux)
6. [Deployment Strategy](#deployment-strategy)
7. [Post-Deployment](#post-deployment)

---

## 🎯 Pre-Deployment Checklist

### Phase 1: Core Functionality Verification (Week 1)

#### Day 1-2: Complete Test Suite Validation
- [ ] **Run full test suite** - Verify all 197 tests pass
  ```bash
  python -m pytest tests/ -v --cov=quarry --cov-report=html
  ```
- [ ] **Fix any failing tests** from refactor
- [ ] **Add missing test coverage** for critical paths
  - [ ] Interactive mode in excavate (mock questionary inputs)
  - [ ] Entry point commands (quarry, quarry.scout, etc.)
  - [ ] Error handling in interactive flows
- [ ] **Integration tests** for real-world scenarios
  - [ ] Run all 14 BI use case tests: `pytest tests/test_bi_use_cases.py -m integration -v`
  - [ ] Verify infinite scroll detection
  - [ ] Test template system (all 15 templates)

#### Day 3-4: Feature Parity Verification
- [ ] **Quarry Suite Tools** - Verify each works end-to-end
  - [ ] Scout: Analyze HTML, detect frameworks, suggest selectors
  - [ ] Survey: Create schemas (interactive + template-based)
  - [ ] Excavate: Extract data (interactive mode + batch mode)
  - [ ] Polish: Deduplicate, transform, validate data
  - [ ] Ship: Export to CSV/JSON/SQLite/Parquet
  
- [ ] **Legacy Wizard Suite** - Verify backward compatibility
  - [ ] `quarry miner` - Initialize workspace
  - [ ] `quarry run job.yml --offline` - Run with fixtures
  - [ ] `quarry run job.yml --live` - Live scraping
  - [ ] `quarry state` - View job state
  - [ ] `quarry wizard` - Interactive job creation

- [ ] **Library API** - Verify programmatic usage
  ```python
  from quarry import get_html, run_job
  from quarry.lib.schemas import load_schema
  from quarry.tools.scout.analyzer import analyze_page
  ```

#### Day 5: Edge Cases & Error Handling
- [ ] **Network failures** - Timeout, connection errors, DNS failures
- [ ] **Invalid inputs** - Malformed HTML, broken schemas, bad URLs
- [ ] **File system issues** - Permissions, disk full, missing directories
- [ ] **Robots.txt compliance** - Blocking, interactive prompts
- [ ] **Rate limiting** - Verify delays work correctly
- [ ] **Pagination edge cases** - Infinite loops, missing "next" links
- [ ] **Character encoding** - UTF-8, Latin-1, special characters
- [ ] **Large files** - Memory management for big HTML/datasets

---

## 🚨 Critical Path Items

### Must-Have Before Deployment

#### 1. Interactive Mode Completion (High Priority)
**Current**: Only excavate has interactive mode  
**Goal**: All tools should offer interactive mode when called without arguments

**Tasks**:
- [ ] **Scout Interactive Mode**
  ```bash
  quarry scout
  # → Analyze URL or file: [URL/Local file]
  # → Enter URL: _
  # → Output format: [Terminal/JSON]
  # → Save to file? [y/N]: _
  ```
  - Implementation: `quarry/tools/scout/cli.py`
  - Add questionary prompts when `url_or_file` is None
  - Preserve `--url`, `--file`, `--format` flags for batch mode

- [ ] **Survey Interactive Mode** (Partially done - enhance)
  ```bash
  quarry survey create
  # → Schema name: _
  # → Use template? [y/N]: _
  # → Template type: [article/product/financial_data/...]
  # → Target URL (optional): _
  # → Output file: schema.yml
  ```
  - Already interactive, but could improve prompts
  - Add better template selection UX
  - Preview before saving

- [ ] **Polish Interactive Mode**
  ```bash
  quarry polish
  # → Input file: _
  # → Operations: [☐ Deduplicate ☐ Transform ☐ Validate]
  # → Dedupe keys: _
  # → Output file: _
  ```
  - Implementation: `quarry/tools/polish/cli.py`
  - Multi-select for operations
  - Conditional prompts based on selections

- [ ] **Ship Interactive Mode**
  ```bash
  quarry ship
  # → Input file: _
  # → Export format: [CSV/JSON/SQLite/Parquet/Excel]
  # → Output destination: _
  # → Options: (format-specific prompts)
  ```
  - Implementation: `quarry/tools/ship/cli.py`
  - Dynamic prompts based on format
  - Validate destination before export

#### 2. Environment Variable Audit (Medium Priority)
**Status**: ✅ Complete - All env vars now use QUARRY_* prefix

**Completed**:
- [x] All env vars updated to QUARRY_* prefix
- [x] No remaining SCRAPESUITE_* references in quarry/ or tests/

#### 3. Repository Rename (Critical for Deployment)
**Status**: ✅ Complete - Repo renamed to `quarry`

**Completed**:
- [x] GitHub repo renamed `scrapesuite` → `quarry`
- [x] GitHub redirect is active
- [x] README.md badge URLs updated
- [x] Documentation links updated

#### 4. PyPI Package Name (Critical)
**Decision needed**: Package name on PyPI

**Options**:
- [ ] Option A: `quarry` (ideal, check availability)
- [ ] Option B: `quarry-web` (if quarry taken)
- [ ] Option C: `web-quarry` (fallback)
- [ ] Option D: `quarry-scraper` (descriptive)

**Tasks**:
- [ ] **Check PyPI availability**: `pip search quarry` (deprecated, check pypi.org)
- [ ] **Reserve name**: Create placeholder package if needed
- [ ] **Update pyproject.toml** with final name
- [ ] **Prepare PyPI deployment**:
  ```bash
  python -m build
  twine check dist/*
  twine upload --repository testpypi dist/*  # Test first
  ```

---

## 🧪 Testing & Validation

### Comprehensive Test Plan

#### Unit Tests (Target: 95% coverage)
- [ ] **Core library** (`quarry/lib/`)
  - [x] HTTP client (test_http_bot_evasion.py - 6 passing)
  - [x] Rate limiting (test_ratelimit.py)
  - [x] Selectors (test_selector_builder.py)
  - [ ] Schemas validation edge cases
  - [ ] Robots.txt parsing edge cases

- [ ] **Framework profiles** (`quarry/framework_profiles/`)
  - [x] Existing tests (test_new_framework_profiles.py, etc.)
  - [ ] Add tests for new ecommerce profiles
  - [ ] Verify scoring algorithm accuracy

- [ ] **Quarry tools**
  - [x] Scout (test_probe.py - 6 passing)
  - [x] Survey (test_blueprint.py)
  - [x] Excavate (test_forge.py)
  - [x] Polish (test_polish.py)
  - [x] Ship (test_crate.py)
  - [ ] Interactive mode tests (with mocked inputs)

#### Integration Tests
- [x] **BI use cases** (test_bi_use_cases.py - 14 scenarios)
- [ ] **End-to-end workflows**
  - [ ] Scout → Survey → Excavate → Polish → Ship pipeline
  - [ ] Template-based schema → extraction → export
  - [ ] Infinite scroll detection → API guide usage
  - [ ] Multi-page pagination extraction

#### Manual Testing (Following MANUAL_TESTING.md)
- [ ] **Part 1: Business Intelligence Features** (Tests 1-10)
- [ ] **Part 2: Quarry Suite Core** (Tests 11-21)
- [ ] **Part 3: Integration Testing - BI Workflows** (Tests 22-24)
- [ ] **Part 4: Infinite Scroll & API Discovery** (Tests 25-28)
- [ ] **Part 5: Error Handling** (Tests 29-30)
- [ ] **Part 6: Integration Tests** (Tests 31-35)
- [ ] **Part 7: Performance & Validation**

#### Cross-Platform Testing
- [ ] **Linux** (Ubuntu 24.04 - current environment) ✅
- [ ] **macOS** (latest)
- [ ] **Windows** (Windows 10/11)
- [ ] **Python versions**: 3.11, 3.12, 3.13

#### Performance Testing
- [ ] **Large datasets** (10K+ items)
- [ ] **Memory usage** profiling
- [ ] **Pagination performance** (100+ pages)
- [ ] **Rate limiting** accuracy under load
- [ ] **Concurrent extraction** (if implemented)

---

## ✨ Feature Completion

### Current Features Audit

#### ✅ Fully Working
- [x] Scout tool (HTML analysis, framework detection)
- [x] Survey tool (schema creation with templates)
- [x] Excavate tool (extraction engine with pagination)
- [x] Polish tool (deduplication, transforms, validation)
- [x] Ship tool (CSV/JSON/SQLite/Parquet export)
- [x] 15 BI templates (financial, real estate, etc.)
- [x] Infinite scroll detection (60%+ confidence)
- [x] API discovery guide (`--find-api`)
- [x] Framework profiles (Bootstrap, React, WordPress, etc.)
- [x] Robots.txt compliance
- [x] Rate limiting
- [x] Legacy wizard suite

#### 🚧 Needs Completion
- [ ] **Interactive modes** for scout/survey/polish/ship
- [ ] **Error recovery** in interactive flows
- [ ] **Progress indicators** for long operations
- [ ] **Configuration file** support (`~/.quarry/config.yml`)
- [ ] **Plugin system** (future - not critical)

#### 🎯 Nice-to-Have (Post v2.0)
- [ ] **Parallel extraction** (multi-threading)
- [ ] **Proxy support** (rotating proxies)
- [ ] **Browser automation** integration (Playwright/Selenium)
- [ ] **Cloud export** (S3, GCS, Azure Blob)
- [ ] **Database sinks** (PostgreSQL, MongoDB)
- [ ] **Webhook notifications** (completion alerts)
- [ ] **Schedule/cron** integration
- [ ] **Web UI** (Flask/FastAPI dashboard)

---

## 📚 Documentation & UX

### Documentation Completion

#### User Documentation
- [x] **README.md** - Quick start, overview ✅
- [x] **MANUAL_TESTING.md** - Comprehensive testing guide ✅
- [x] **CONTRIBUTING.md** - Development guide ✅
- [x] **REFACTOR_SUMMARY.md** - Migration guide ✅
- [ ] **INSTALLATION.md** - Detailed install instructions
  - System requirements
  - Virtual environment setup
  - Troubleshooting common issues
  - Platform-specific notes

- [ ] **USAGE_GUIDE.md** - Comprehensive user manual
  - Getting started tutorial
  - Tool-by-tool deep dive
  - Common workflows
  - Real-world examples
  - FAQ section

- [ ] **API_REFERENCE.md** - Library API documentation
  - Module organization
  - Function signatures
  - Code examples
  - Type hints

- [ ] **TEMPLATES.md** - Template system guide
  - All 15 templates documented
  - When to use each template
  - Customization examples
  - Creating custom templates

#### Developer Documentation
- [x] **ARCHITECTURE_V2.md** - System design ✅
- [x] **QUARRY_COMPLETE.md** - Quarry suite overview ✅
- [x] **INFINITE_SCROLL_API_GUIDE.md** - API discovery ✅
- [ ] **PLUGIN_DEVELOPMENT.md** - Plugin API (future)
- [ ] **TESTING_GUIDE.md** - Testing best practices
  - Unit test structure
  - Integration test patterns
  - Mocking strategies
  - Coverage requirements

#### Code Documentation
- [ ] **Docstrings audit** - All public APIs documented
  - Module-level docstrings
  - Class docstrings
  - Function/method docstrings
  - Type hints everywhere
  - Examples in docstrings

- [ ] **Type hints completion** - Gradual typing to 100%
  - Currently: framework_profiles, http have typed defs
  - Complete typing for all modules
  - Enable strict mypy checking

### User Experience Improvements

#### CLI Enhancements
- [ ] **Better help text** - More examples, clearer descriptions
- [ ] **Error messages** - Actionable suggestions
  ```
  ❌ Error: Schema file not found: schema.yml
  
  💡 Did you mean:
     • /path/to/schemas/schema.yml
     • Create new: quarry survey create schema.yml
  ```

- [ ] **Progress bars** for long operations
  ```python
  from rich.progress import Progress
  # Add to pagination, large file processing
  ```

- [ ] **Colored output** (already using Rich, enhance)
  - Success: Green
  - Warnings: Yellow
  - Errors: Red
  - Info: Blue

- [ ] **Confirmation prompts** for destructive operations
  ```
  ⚠️  This will overwrite existing file: output.csv
  Continue? [y/N]:
  ```

#### Interactive Mode UX
- [ ] **Smart defaults** based on context
  - Suggest file names from schema name
  - Detect file types automatically
  - Remember recent choices

- [ ] **Validation feedback** in real-time
  ```
  Schema file: invalid.yml
  ❌ File does not exist
  Schema file: _
  ```

- [ ] **Autocomplete** for file paths (questionary supports this)

- [ ] **Keyboard shortcuts** documentation
  ```
  Use ↑↓ arrows to navigate, Enter to select, Ctrl+C to cancel
  ```

---

## 🚀 Deployment Strategy

### Phase 1: Pre-Release Testing (Week 2)

#### Alpha Release (Internal)
- [ ] **Merge to main branch**
  ```bash
  git checkout main
  git merge refactor-to-quarry
  git tag v2.0.0-alpha.1
  git push origin main --tags
  ```

- [ ] **Install from source** testing
  ```bash
  pip install git+https://github.com/russellbomer/quarry.git@v2.0.0-alpha.1
  ```

- [ ] **Docker image** (optional but recommended)
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY . .
  RUN pip install -e .
  ENTRYPOINT ["quarry"]
  ```

- [ ] **Documentation site** (optional - GitHub Pages)
  - Use MkDocs or Sphinx
  - Deploy to quarry.readthedocs.io or GitHub Pages
  - API documentation from docstrings

#### Beta Release (Limited Users)
- [ ] **Tag beta release** `v2.0.0-beta.1`
- [ ] **Share with test users** (5-10 people)
- [ ] **Collect feedback** via GitHub Issues
- [ ] **Fix critical bugs** found in testing
- [ ] **Update docs** based on feedback

### Phase 2: Release Candidate (Week 3)

#### RC Preparation
- [ ] **All tests passing** on all platforms
- [ ] **All interactive modes** implemented
- [ ] **Documentation complete** (user guide, API reference)
- [ ] **CHANGELOG.md** - Complete release notes
  ```markdown
  # Changelog
  
  ## [2.0.0] - 2025-11-XX
  
  ### Breaking Changes
  - Package renamed from scrapesuite to quarry
  - All imports changed to use `quarry` namespace
  - Environment variables renamed SCRAPESUITE_* → QUARRY_*
  
  ### Added
  - Interactive mode for all tools
  - 15 BI templates for common use cases
  - Infinite scroll detection
  - API discovery guide
  - Clean entry points (quarry, quarry.scout, etc.)
  
  ### Changed
  - Improved error messages
  - Better progress indicators
  - Enhanced documentation
  
  ### Fixed
  - (List bug fixes)
  ```

- [ ] **Tag RC** `v2.0.0-rc.1`
- [ ] **Final testing** - Run full manual test suite
- [ ] **Security audit** - Check dependencies
  ```bash
  pip install safety
  safety check
  ```

### Phase 3: Production Release (Week 4)

#### PyPI Deployment
- [ ] **Build distribution**
  ```bash
  python -m build
  ls dist/
  # quarry-2.0.0.tar.gz
  # quarry-2.0.0-py3-none-any.whl
  ```

- [ ] **Upload to PyPI**
  ```bash
  twine upload dist/*
  ```

- [ ] **Verify installation**
  ```bash
  pip install quarry
  quarry --version  # Should show 2.0.0
  ```

- [ ] **Tag final release** `v2.0.0`
  ```bash
  git tag -a v2.0.0 -m "Release v2.0.0: Complete package refactor and feature set"
  git push origin v2.0.0
  ```

#### GitHub Release
- [ ] **Create GitHub release** from tag
- [ ] **Release notes** (copy from CHANGELOG.md)
- [ ] **Attach binaries** (optional - wheels)
- [ ] **Migration guide** link in release notes

#### Announcement
- [ ] **Blog post** (if you have one)
- [ ] **Social media** (Twitter, LinkedIn, Reddit r/python)
- [ ] **Python Weekly** submission
- [ ] **Hacker News** (if appropriate)
- [ ] **Dev.to** article

---

## 📊 Post-Deployment

### Monitoring & Maintenance

#### Week 1 Post-Release
- [ ] **Monitor GitHub Issues** - Respond within 24 hours
- [ ] **Track PyPI downloads** - pip install stats
- [ ] **User feedback** - Collect via issues, email, social
- [ ] **Hot fixes** - Patch critical bugs immediately
  - Version bump: 2.0.1, 2.0.2, etc.

#### Month 1 Post-Release
- [ ] **Feature requests** - Triage and prioritize
- [ ] **Documentation improvements** - Based on common questions
- [ ] **Performance optimizations** - Based on user reports
- [ ] **Platform-specific fixes** - Windows/macOS issues

### Roadmap Planning (v2.1+)

#### High Priority (v2.1 - 1-2 months)
- [ ] **Parallel extraction** - Speed up large scraping jobs
- [ ] **Proxy support** - Rotating proxies for scale
- [ ] **Database exports** - PostgreSQL, MySQL, MongoDB
- [ ] **More templates** - Based on user requests
- [ ] **Plugin system** - Allow custom connectors/transforms

#### Medium Priority (v2.2 - 3-4 months)
- [ ] **Browser automation** - Playwright integration for JS-heavy sites
- [ ] **Cloud exports** - S3, GCS, Azure Blob Storage
- [ ] **Scheduling** - Cron-like job scheduling
- [ ] **Web UI** - Browser-based dashboard
- [ ] **API server** - REST API for remote extraction

#### Low Priority (v3.0 - 6+ months)
- [ ] **Machine learning** - Auto-detect selectors
- [ ] **Distributed extraction** - Multi-machine coordination
- [ ] **Real-time streaming** - WebSocket/SSE support
- [ ] **Commercial features** - Enterprise authentication, team management

---

## ⚡ Quick Action Items (This Week)

### Critical (Do First)
1. [ ] **Run full test suite** and fix any failures
2. [ ] **Complete interactive modes** for scout/polish/ship
3. [ ] **Test all 15 BI templates** with real websites
4. [ ] **Verify all entry points** work correctly

### Important (Do Next)
5. [ ] **Write INSTALLATION.md** and USAGE_GUIDE.md
6. [ ] **Complete docstrings** for public APIs
7. [ ] **Run manual testing plan** (MANUAL_TESTING.md)
8. [ ] **Check PyPI package name** availability

### Nice-to-Have (If Time)
9. [ ] **Add progress bars** to long operations
10. [ ] **Improve error messages** with suggestions
11. [ ] **Create Docker image**
12. [ ] **Set up documentation site**

---

## 📅 Timeline Summary

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| **Week 1** | Testing & Feature Completion | All tests passing, interactive modes done, docs complete |
| **Week 2** | Alpha/Beta Testing | Tag releases, gather feedback, fix bugs |
| **Week 3** | Release Candidate | Final testing, security audit, RC tag |
| **Week 4** | Production Release | PyPI deploy, GitHub release, announcements |

**Target Launch Date**: End of Week 4 (approximately 4 weeks from now)

---

## ✅ Definition of Done (Production Ready)

### Code Quality
- ✅ All 197+ unit tests passing
- ✅ Integration tests passing
- ✅ Manual test suite completed
- ✅ 90%+ code coverage
- ✅ No critical bugs
- ✅ Type hints on all public APIs
- ✅ Docstrings on all public functions

### Features
- ✅ All 5 Quarry tools fully functional
- ✅ Interactive mode for all tools
- ✅ 15 BI templates working
- ✅ Infinite scroll detection
- ✅ Legacy wizard suite working
- ✅ Entry points installed correctly

### Documentation
- ✅ README.md complete
- ✅ INSTALLATION.md complete
- ✅ USAGE_GUIDE.md complete
- ✅ API_REFERENCE.md complete
- ✅ CHANGELOG.md up to date
- ✅ All examples tested

### Deployment
- ✅ PyPI package published
- ✅ GitHub release created
- ✅ Migration guide available
- ✅ Announcement posted

**When all boxes checked → Ship it! 🚀**

---

## 🆘 Risk Mitigation

### Identified Risks

1. **PyPI Name Conflict**
   - Risk: `quarry` name might be taken
   - Mitigation: Check now, have backup names ready
   - Fallback: `quarry-web`, `web-quarry`, `quarry-scraper`

2. **Breaking Changes Impact**
   - Risk: Users on scrapesuite might break
   - Mitigation: Keep scrapesuite branch maintained for 3-6 months
   - Communication: Clear migration guide, deprecation warnings

3. **Platform-Specific Bugs**
   - Risk: Code works on Linux but not Windows/macOS
   - Mitigation: Test on all platforms before release
   - CI/CD: GitHub Actions matrix for cross-platform testing

4. **Performance Issues**
   - Risk: Interactive mode too slow on large files
   - Mitigation: Profile and optimize hot paths
   - Testing: Benchmark with large datasets

5. **Documentation Gaps**
   - Risk: Users can't figure out how to use features
   - Mitigation: Comprehensive docs, examples, tutorials
   - Feedback: Beta testing with non-developers

---

**Last Updated**: November 13, 2025  
**Next Review**: After Week 1 testing complete  
**Owner**: @russellbomer
