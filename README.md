# sancheck

**Repository**: https://github.com/fozagtx/sancheck

`sancheck` is a real URL security scanner, link gate, and Codex plugin package. It checks links before an agent workflow, build script, or developer tool opens them, with specific handling for prompt-injection text hidden in fetched pages.

No mock verdicts are used. Network checks are live. Google Safe Browsing, VirusTotal, and PhishTank run only when real API credentials are present; otherwise their checks are reported as `skipped`.

## 📚 Documentation

- 📖 **[How Codex & GPT-5.6 Were Used](CODEX_USAGE.md)** - Detailed breakdown of Codex usage, development workflow, and key decisions
- 📦 **[Installation & Setup Guide](INSTALL.md)** - Full installation instructions, supported platforms, and testing guide

## Built with Codex

**Codex Session ID**: `019f8658-5272-7480-ae44-3a4ebd620ba2`

Built using Codex with GPT-5.6:
- URL validation and normalization logic
- DNS resolution and SSRF protection
- TLS certificate validation
- HTTP behavior analysis
- Prompt injection detection patterns
- Threat intel provider integrations
- CLI interface and middleware contract

## What It Checks

- URL structure: userinfo tricks, IP literals, uncommon ports, suspicious keywords, long or encoded paths.
- DNS and SSRF safety: loopback, private, link-local, multicast, reserved, and unspecified IPs are blocked by default.
- HTTPS/TLS: certificate chain and expiration are checked for HTTPS URLs.
- HTTP behavior: redirects, status codes, content type, headers, and final targets are inspected.
- Prompt injection: bounded page text and HTML samples are scanned without executing page scripts.
- Reputation: shorteners, risky-looking hosts, new domains via RDAP, and optional live providers.

## Quick Start

Scan one URL:

```sh
PYTHONPATH=src python3 -m sancheck scan https://example.com --format text
```

Use the middleware contract:

```sh
printf 'check https://example.com' | ./scripts/sancheck-gate
```

Gate links from a prompt or Markdown file:

```sh
PYTHONPATH=src python3 -m sancheck gate --stdin --format json < message.md
```

Exit codes:

- `0`: all scanned links are allowed.
- `2`: at least one link is blocked by policy.
- `1`: scanner usage or runtime failure.

## Codex Plugin Package

The repo includes a bundled plugin at:

```text
plugins/sancheck
```

The plugin contains:

- `.codex-plugin/plugin.json` - Plugin manifest
- `skills/url-gate/SKILL.md` - URL gate skill for Codex
- `scripts/sancheck-gate` - Gate script entry point
- Bundled scanner source under `scripts/src/sancheck`

### Using the Plugin

The bundled gate works without installing the Python package:

```sh
# Scan from stdin (text or JSON)
printf '{"text":"open https://example.com"}' | plugins/sancheck/scripts/sancheck-gate

# Scan a URL directly
plugins/sancheck/scripts/sancheck-gate https://example.com

# Gate URLs from a file
cat urls.txt | plugins/sancheck/scripts/sancheck-gate
```

The plugin emits JSON and exits with:
- `0`: all scanned links are allowed
- `2`: at least one link is blocked by policy
- `1`: scanner usage or runtime failure

### Plugin Integration with Codex

When Codex encounters a task with external URLs, the `url-gate` skill automatically:
1. Extracts URLs from the task context
2. Sends them to `sancheck-gate` for validation
3. Blocks the operation if any URL is flagged as unsafe
4. Returns the scan results to Codex

Example Codex task:
```
Fetch the content from https://example.com and summarize it
```

Codex will automatically gate the URL before fetching, ensuring the link is safe.

## Optional Provider Keys

Set any of these environment variables to enable the corresponding live provider:

```sh
export GOOGLE_SAFE_BROWSING_API_KEY="..."
export VIRUSTOTAL_API_KEY="..."
export PHISHTANK_APP_KEY="..."
```

Provider failures and missing keys stay visible in the report. They are not converted into clean results.

## Landing Page

The web project is a static landing page for the tool, not the scanner runtime:

```sh
npm install
npm run dev
```

Build and preview:

```sh
npm run build
npm run preview
```

## Tests

```sh
npm run check
```

The tests use a real local HTTP server and deterministic local content. They do not mock scanner verdicts or external provider responses.
