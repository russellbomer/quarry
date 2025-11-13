# Quarry Codebase Cleanup & Consolidation Plan

**Date**: November 10, 2025  
**Branch**: chore/context-freeze  
**Current State**: 115 tests passing, confidence scoring implemented, expanded field types added

---

## 1. Documentation Consolidation

### A. Root-Level Documentation (Too Many Files)

**Current state**: 6 markdown files in root
- `README.md` - Main entry point ✅ KEEP
- `QUICKSTART.md` - Quick start guide
- `WIZARD_USAGE.md` - Wizard-specific usage
- `TROUBLESHOOTING.md` - Troubleshooting
- `BLIND_TEST_GUIDE.md` - Testing guide
- `FIRST_RUN.md` - First run instructions

**Action**:
1. **Consolidate into README.md**:
   - Merge QUICKSTART.md → README.md "Quick Start" section
   - Merge FIRST_RUN.md → README.md "Installation" section
   - Move detailed wizard usage to docs/WIZARD.md
   - Move troubleshooting to docs/TROUBLESHOOTING.md
   - Move testing to docs/TESTING.md

2. **Result**: Single README.md with sections:
   - Installation
   - Quick Start
   - Basic Usage
   - Examples
   - Links to detailed docs/

### B. Docs Directory Organization

**Current docs/**: 11 files, some outdated
```
ARCHITECTURE_LIMITATIONS.md     - Keep, useful context
BOT_EVASION.md                  - Keep, important security info
CONNECTOR_GENERATOR_SUMMARY.md  - Archive or delete (old?)
FRAMEWORK_INTEGRATION.md        - ✅ Keep, recently updated
FRAMEWORK_PROFILES_ANALYSIS.md  - ✅ Keep, strategic document
QUICK_TEST.md                   - Consolidate into TESTING.md
SESSION_2025-11-09.md           - Archive (session note)
SESSION_NOTES.md                - Archive (development log)
TESTING_GUIDE.md                - Keep, comprehensive
WIZARD_DEVELOPMENT_LOG.md       - Archive (development log)
YAML_SELECTORS_VISION.md        - Archive (vision doc, mostly implemented)
```

**Action**:
1. Create `docs/archive/` for historical documents
2. Move session notes and dev logs to archive
3. Consolidate testing documents
4. Create organized structure:
   ```
   docs/
   ├── README.md (index to all docs)
   ├── ARCHITECTURE.md (consolidate ARCHITECTURE_LIMITATIONS.md)
   ├── FRAMEWORK_PROFILES.md (consolidate FRAMEWORK_INTEGRATION + ANALYSIS)
   ├── TESTING.md (consolidate TESTING_GUIDE + QUICK_TEST)
   ├── TROUBLESHOOTING.md (move from root)
   ├── WIZARD.md (move WIZARD_USAGE from root)
   ├── SECURITY.md (rename BOT_EVASION)
   └── archive/
       ├── SESSION_2025-11-09.md
       ├── SESSION_NOTES.md
       ├── WIZARD_DEVELOPMENT_LOG.md
       ├── YAML_SELECTORS_VISION.md
       └── CONNECTOR_GENERATOR_SUMMARY.md
   ```

### C. Internal Directive Files

**Current**: 4 .txt files in root with internal directives
- `quarry_cleanup.txt`
- `quarry_conscientious_prompt.txt`
- `quarry_eod_directive.txt`
- `quarry_master_directive.txt`

**Action**:
1. Move to `.internal/` directory (git ignored)
2. These are development aids, not part of project

---

## 2. Test Files Cleanup

### A. Root-Level Test Scripts

**Current**: Debug/test scripts in root
- `debug_fda_live.py` - Development debug script
- `test_fda_inspector.py` - Old test
- `test_inspector.py` - Old test

**Action**:
1. Move to `scripts/debug/` or delete if obsolete
2. If still useful, add to `scripts/`
3. Root should only have production files

### B. Test Coverage Gaps

**Current**: 115 tests, good coverage

**Action**:
1. Add integration tests for complete workflow
2. Add tests for edge cases in confidence scoring
3. Add benchmarks for performance

---

## 3. Code Refactoring

### A. Framework Profiles Organization

**Current**: Single 1,100+ line file `framework_profiles.py`

**Issues**:
- Hard to navigate
- Will grow to 3,000+ lines with 30+ profiles
- Mixing profile definitions with utility functions

**Action**:
```python
quarry/framework_profiles/
├── __init__.py          # Exports, detect_framework, detect_all_frameworks
├── base.py              # FrameworkProfile base class
├── cms/
│   ├── __init__.py
│   ├── drupal.py       # DrupalViewsProfile
│   ├── wordpress.py    # WordPressProfile
│   └── ghost.py        # GhostProfile (future)
├── frameworks/
│   ├── __init__.py
│   ├── django.py       # DjangoAdminProfile
│   ├── react.py        # ReactComponentProfile
│   ├── vue.py          # VueJSProfile
│   ├── nextjs.py       # NextJSProfile
│   └── angular.py      # AngularProfile (future)
├── css/
│   ├── __init__.py
│   ├── bootstrap.py    # BootstrapProfile
│   └── tailwind.py     # TailwindProfile
├── ecommerce/
│   ├── __init__.py
│   ├── shopify.py      # ShopifyProfile
│   └── woocommerce.py  # WooCommerceProfile (future)
└── universal/
    ├── __init__.py
    ├── schema_org.py   # SchemaOrgProfile (future)
    └── social_meta.py  # SocialMetaProfile (future)
```

**Benefits**:
- Easier to find profiles
- Can add profiles without merge conflicts
- Clear categorization
- Better imports

### B. Inspector Optimization

**File**: `inspector.py` (1,579 lines)

**Issues**:
- Some repeated DOM traversal
- Could cache BeautifulSoup objects
- Some functions too long

**Action**:
1. Profile with real-world HTML (100KB+ samples)
2. Add caching for repeated operations
3. Split into modules:
   ```python
   quarry/inspector/
   ├── __init__.py
   ├── core.py           # Main inspection functions
   ├── strategies.py     # Detection strategies
   ├── selectors.py      # Selector generation
   └── caching.py        # Cache mechanisms
   ```

### C. Type Annotations Consistency

**Current**: Some functions lack type hints

**Action**:
1. Add type hints to all public functions
2. Run mypy for type checking
3. Add to CI/CD pipeline

---

## 4. Configuration & Build

### A. Pyproject.toml

**Current**: Good state

**Action**:
1. Add mypy configuration
2. Add coverage thresholds
3. Document all tool configurations

### B. Makefile

**Current**: Has format, check, test targets

**Action**:
1. Add `make docs` to build documentation
2. Add `make clean` to remove caches
3. Add `make benchmark` for performance tests

---

## 5. Examples & Jobs

### A. Examples Directory

**Current**: Job YAML files in `examples/jobs/`

**Action**:
1. Add README explaining each example
2. Add Python script examples
3. Add CLI usage examples

### B. Scripts Directory

**Current**: `build_batches.py`, `build_profiles.py`

**Action**:
1. Add docstrings
2. Add CLI help
3. Move debug scripts here

---

## 6. Git & GitHub

### A. .gitignore

**Action**:
1. Add `.internal/` for directive files
2. Add coverage reports
3. Add benchmark outputs

### B. GitHub Actions (if exists)

**Action**:
1. Add CI for tests
2. Add linting check
3. Add coverage reporting

---

## 7. Performance Optimizations

### A. Caching Strategy

**Action**:
1. Cache compiled regex patterns in profiles
2. Cache BeautifulSoup parsing
3. Add LRU cache for repeated operations

### B. Lazy Loading

**Action**:
1. Load profiles on-demand
2. Don't import all profiles upfront
3. Reduce startup time

---

## Execution Order

### Phase 1: Documentation (2-3 hours)
1. Create docs/archive/ and move historical files
2. Consolidate root markdown into README.md
3. Reorganize docs/ directory
4. Create docs/README.md index

### Phase 2: File Cleanup (1 hour)
1. Move internal directives to .internal/
2. Move/delete debug scripts
3. Update .gitignore

### Phase 3: Code Refactoring (3-4 hours)
1. Split framework_profiles.py into module
2. Add comprehensive type hints
3. Optimize inspector.py

### Phase 4: Testing & CI (2 hours)
1. Add integration tests
2. Add benchmarks
3. Configure mypy

### Phase 5: Documentation Update (1 hour)
1. Update all docs with new structure
2. Add API documentation
3. Add contribution guide

---

## Success Criteria

✅ All documentation in logical locations  
✅ No debug/directive files in root  
✅ Code organized into clear modules  
✅ Type hints on all public APIs  
✅ All tests passing (target: 130+)  
✅ Clean git history  
✅ Clear contribution path  

---

## Notes

- Keep backward compatibility where possible
- Update imports gradually
- Test at each step
- Commit frequently with clear messages
