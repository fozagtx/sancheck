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

# Keys: copy .env.example to .env in the repo root (or plugin folder)
cp .env.example .env

# Plugin check (paste each line whole; do not split --format or URLs)
plugins/sancheck/scripts/sancheck-gate https://github.com
plugins/sancheck/scripts/sancheck-gate https://testsafebrowsing.appspot.com/s/malware.html; echo exit:$?
```

Expect allow on github (`exit 0`), block on the Safe Browsing malware test URL (`exit 2`, `google_safe_browsing: match`).

To install the plugin in Codex:
1. Copy the `plugins/sancheck` directory to your Codex plugins folder
2. Or symlink it: `ln -s $(pwd)/plugins/sancheck ~/.codex/plugins/sancheck`
3. Put API keys on your PC in a local `.env` (not in the Codex app UI, and not pasted into chat), for example:
   - `~/.codex/plugins/sancheck/.env`, or
   - `.env` in the project folder you open with Codex
4. Copy from `.env.example` and set values as `NAME=your_api_key_here` (replace the placeholder with the real key)
5. Restart Codex to load the plugin

In Codex chat the agent runs `sancheck-gate` locally. Keys are read from `.env` on disk. The chat gets the JSON decision/report only, not the key strings.

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

Paste each command as one full line. Prefer `--format=json` with an `=` so line wraps cannot break the flag.

```bash
# Allow (providers should be clean, not skipped, when .env is set)
PYTHONPATH=src python3 -m sancheck scan https://github.com --format=json

# Block (Google Safe Browsing official test URL)
PYTHONPATH=src python3 -m sancheck scan https://testsafebrowsing.appspot.com/s/malware.html --format=json; echo exit:$?

# SSRF
PYTHONPATH=src python3 -m sancheck scan http://127.0.0.1 --format=json; echo exit:$?
```

### Test the Plugin

```bash
plugins/sancheck/scripts/sancheck-gate https://github.com
plugins/sancheck/scripts/sancheck-gate https://testsafebrowsing.appspot.com/s/malware.html; echo exit:$?
printf '%s' '{"text":"open https://github.com"}' | plugins/sancheck/scripts/sancheck-gate
```
