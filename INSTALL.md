## Installation

**API keys for testing:** [testing keys](https://docs.google.com/document/d/1Ga4IVy5-57BDiO3-JpJu5cgq1fnJpm1Vb943fnYOWB0/edit?usp=sharing)

### As a Python Package

```bash
# Clone the repository
git clone https://github.com/fozagtx/sancheck.git
cd sancheck

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

After installation, you can run sancheck from anywhere:

```bash
sancheck scan https://example.com --format json
sancheck gate --stdin < urls.txt
```

### As a Codex Plugin

The plugin is self-contained and doesn't require Python package installation:

```bash
# Clone the repository
git clone https://github.com/fozagtx/sancheck.git
cd sancheck

# The plugin is ready to use at:
# plugins/sancheck/

# Test it works:
plugins/sancheck/scripts/sancheck-gate https://example.com
```

To install the plugin in Codex:
1. Copy the `plugins/sancheck` directory to your Codex plugins folder
2. Or symlink it: `ln -s $(pwd)/plugins/sancheck ~/.codex/plugins/sancheck`
3. Put API keys on your PC in a local `.env` (not in the Codex app UI), for example:
   - `~/.codex/plugins/sancheck/.env`, or
   - `.env` in the project folder you open with Codex
4. Copy from `.env.example`, fill `VIRUSTOTAL_API_KEY` / `GOOGLE_SAFE_BROWSING_API_KEY` / `PHISHTANK_APP_KEY`
5. Restart Codex to load the plugin

## Supported Platforms

**Operating Systems:**
- macOS (tested on macOS 13+)
- Linux (tested on Ubuntu 20.04+, Debian 11+)
- Windows (via WSL2 or Git Bash)

**Python Versions:**
- Python 3.9+
- Python 3.10+
- Python 3.11+
- Python 3.12+

**Dependencies:**
- Zero external Python dependencies (uses only standard library)
- Node.js 18+ (only for the landing page UI, not required for the scanner)

**Network Requirements:**
- Internet connection for DNS resolution and HTTP requests

## Testing

### Run All Tests

```bash
# From the project root
npm run check
```

This runs:
- Python unit tests
- Python syntax checks
- TypeScript compilation
- Vite build

### Run Python Tests Only

```bash
PYTHONPATH=src python3 -m pytest tests/ -v
```

### Test the Scanner

```bash
# Test with a safe URL
PYTHONPATH=src python3 -m sancheck scan https://example.com --format json

# Test with a private IP (should block)
PYTHONPATH=src python3 -m sancheck scan http://127.0.0.1 --format json

# Test the middleware contract
printf 'check https://example.com' | ./scripts/sancheck-gate
```

### Test with API Keys

```bash
# Test with VirusTotal
export VIRUSTOTAL_API_KEY="your-key-here"
PYTHONPATH=src python3 -m sancheck scan https://example.com --format json

# Test with Google Safe Browsing
export GOOGLE_SAFE_BROWSING_API_KEY="your-key-here"
PYTHONPATH=src python3 -m sancheck scan https://example.com --format json
```

### Test the Plugin

```bash
# Test plugin gate script
plugins/sancheck/scripts/sancheck-gate https://example.com

# Test with stdin
echo "Check https://example.com" | plugins/sancheck/scripts/sancheck-gate

# Test with JSON input
echo '{"text": "open https://example.com"}' | plugins/sancheck/scripts/sancheck-gate
```
