# Quarry Installation Guide

Complete installation instructions for **Quarry** - a modern web data extraction toolkit.

---

## 📦 Quick Start

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **pip** (included with Python)
- **Internet connection** (for package installation)

### Install from PyPI (Recommended)

```bash
pip install quarry
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/russellbomer/quarry.git
cd quarry

# Install in editable mode
pip install -e .
```

### Verify Installation

```bash
# Check version
quarry --version
# Output: quarry, version 2.0.0

# View available tools
quarry --help
```

---

## 🖥️ Platform-Specific Instructions

### Linux (Ubuntu/Debian)

```bash
# Update package lists
sudo apt update

# Install Python 3.12 (if not installed)
sudo apt install python3.12 python3.12-venv python3-pip

# Create virtual environment (recommended)
python3.12 -m venv quarry-env
source quarry-env/bin/activate

# Install Quarry
pip install quarry

# Verify
quarry --version
```

### macOS

```bash
# Install Python 3.12 using Homebrew
brew install python@3.12

# Create virtual environment
python3.12 -m venv quarry-env
source quarry-env/bin/activate

# Install Quarry
pip install quarry

# Verify
quarry --version
```

### Windows

```powershell
# Install Python 3.12 from python.org
# Then in PowerShell or Command Prompt:

# Create virtual environment
python -m venv quarry-env
quarry-env\Scripts\activate

# Install Quarry
pip install quarry

# Verify
quarry --version
```

---

## 🐍 Virtual Environments (Recommended)

Using a virtual environment isolates Quarry's dependencies from your system Python.

### Create and Activate

**Linux/macOS:**
```bash
python3 -m venv quarry-env
source quarry-env/bin/activate
```

**Windows:**
```powershell
python -m venv quarry-env
quarry-env\Scripts\activate
```

### Deactivate

```bash
deactivate
```

### Why Use Virtual Environments?

- ✅ Avoid dependency conflicts
- ✅ Easy to delete and recreate
- ✅ Isolate project dependencies
- ✅ Reproducible environments

---

## 📚 Dependencies

Quarry automatically installs these dependencies:

### Core Dependencies
- **requests** - HTTP client
- **beautifulsoup4** - HTML parsing
- **lxml** - Fast XML/HTML parser
- **pyyaml** - YAML configuration support

### Data Processing
- **pandas** - Data manipulation
- **pyarrow** - Parquet file support

### CLI & UX
- **click** - Command-line interface framework
- **questionary** - Interactive prompts
- **rich** - Terminal formatting
- **typer** - Additional CLI utilities

### Validation
- **pydantic** - Data validation

---

## ⚙️ Development Installation

For contributing or development:

```bash
# Clone repository
git clone https://github.com/russellbomer/quarry.git
cd quarry

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e .
pip install pytest pytest-cov ruff mypy

# Run tests
pytest

# Run linter
ruff check .

# Format code
ruff format .
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "command not found: quarry"

**Cause**: Entry points not in PATH

**Solutions**:
```bash
# Option 1: Reinstall with pip
pip uninstall quarry
pip install quarry

# Option 2: Use python -m
python -m quarry.quarry --help

# Option 3: Add to PATH (check pip install location)
pip show -f quarry
```

#### 2. "ModuleNotFoundError: No module named 'quarry'"

**Cause**: Not installed or wrong Python environment

**Solutions**:
```bash
# Verify installation
pip list | grep quarry

# Install if missing
pip install quarry

# Check Python version
python --version  # Should be 3.11+
```

#### 3. "ImportError: cannot import name..."

**Cause**: Partial installation or conflicting packages

**Solutions**:
```bash
# Reinstall from scratch
pip uninstall quarry
pip cache purge
pip install quarry
```

#### 4. Permission Errors (Linux/macOS)

**Cause**: Trying to install system-wide without sudo

**Solutions**:
```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv quarry-env
source quarry-env/bin/activate
pip install quarry

# Option 2: User install (not recommended)
pip install --user quarry

# Option 3: System install (requires sudo)
sudo pip install quarry
```

#### 5. SSL Certificate Errors

**Cause**: Corporate proxy or outdated certificates

**Solutions**:
```bash
# Option 1: Upgrade certifi
pip install --upgrade certifi

# Option 2: Use trusted host (temporary workaround)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org quarry
```

#### 6. "lxml installation failed"

**Cause**: Missing system libraries

**Solutions**:

**Ubuntu/Debian:**
```bash
sudo apt install python3-dev libxml2-dev libxslt1-dev zlib1g-dev
pip install quarry
```

**macOS:**
```bash
brew install libxml2 libxslt
pip install quarry
```

**Windows:**
- Install from precompiled wheels (usually automatic)
- Or install Visual Studio Build Tools

---

## 🧪 Verify Installation

Run these commands to ensure everything works:

```bash
# 1. Check version
quarry --version

# 2. Test each tool
quarry.scout --help
quarry.survey --help
quarry.excavate --help
quarry.polish --help
quarry.ship --help

# 3. Run a quick test
echo '<html><h1>Test</h1></html>' > test.html
quarry scout test.html
rm test.html
```

**Expected output**: No errors, help text displays correctly

---

## 🔄 Upgrading

### Upgrade to Latest Version

```bash
pip install --upgrade quarry
```

### Upgrade from scrapesuite v1.x

Quarry v2.0 is a complete rewrite with breaking changes:

**Old commands** (scrapesuite v1.x):
```bash
python -m scrapesuite.probe https://example.com
python -m scrapesuite.blueprint schema.yml
python -m scrapesuite.forge schema.yml
```

**New commands** (Quarry v2.0):
```bash
quarry scout https://example.com
quarry.survey create
quarry.excavate schema.yml
```

**Migration steps**:
1. Uninstall old version: `pip uninstall scrapesuite`
2. Install Quarry: `pip install quarry`
3. Update scripts/workflows with new command names
4. Review [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) for detailed changes

---

## 🐳 Docker Installation (Alternative)

Coming soon! Docker images will be available for easy deployment.

```bash
# Pull image (future)
docker pull russellbomer/quarry:2.0

# Run container (future)
docker run -it russellbomer/quarry:2.0 quarry.scout https://example.com
```

---

## 💻 IDE Integration

### VS Code

Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "python.testing.pytestEnabled": true
}
```

### PyCharm

1. File → Settings → Project → Python Interpreter
2. Add virtual environment: `quarry-env`
3. Mark `quarry/` as Sources Root
4. Configure pytest as test runner

---

## 📊 System Requirements

### Minimum
- Python 3.11+
- 512 MB RAM
- 50 MB disk space

### Recommended
- Python 3.12+
- 2 GB RAM
- 200 MB disk space (includes cache)

### Supported Platforms
- ✅ Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)
- ✅ macOS (11.0+, Intel & Apple Silicon)
- ✅ Windows (10+, 64-bit)

---

## 🆘 Getting Help

- **Documentation**: [GitHub Wiki](https://github.com/russellbomer/quarry/wiki)
- **Issues**: [GitHub Issues](https://github.com/russellbomer/quarry/issues)
- **Discussions**: [GitHub Discussions](https://github.com/russellbomer/quarry/discussions)
- **Email**: support@quarry.dev *(coming soon)*

---

## ✅ Next Steps

After installation:

1. **Read the [USAGE_GUIDE.md](USAGE_GUIDE.md)** - Learn how to use each tool
2. **Try the examples** - Run `quarry scout https://example.com`
3. **Check [MANUAL_TESTING.md](MANUAL_TESTING.md)** - Hands-on tutorials
4. **Join the community** - Share feedback and contribute

Happy quarrying! 🪨⛏️
