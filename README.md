# seccheck

`seccheck` is a real URL security scanner and link gate. It checks links before an agent or developer opens them, with special attention to prompt-injection text hidden in fetched pages.

No mock verdicts are used. Network checks are live. Google Safe Browsing, VirusTotal, and PhishTank are called only when you provide real API credentials; otherwise their checks are reported as `skipped`.

## What It Checks

- URL structure: userinfo tricks, IP literals, uncommon ports, suspicious keywords, long/encoded paths.
- DNS and SSRF safety: resolves hosts and blocks loopback, private, link-local, multicast, reserved, and unspecified IPs by default.
- HTTPS/TLS: validates the certificate chain and expiration for HTTPS URLs.
- HTTP health: follows redirects safely, checks status codes, content type, headers, and redirect targets.
- Prompt injection: fetches a bounded, non-executed content sample and flags hostile instructions such as attempts to override system/developer instructions, leak secrets, run tools, or hide instructions in comments/styles.
- Reputation: checks shorteners, risky-looking hostnames, new domains via RDAP when available, and optional external threat-intel providers.

## Quick Start

Run directly from the repo:

```sh
PYTHONPATH=src python3 -m seccheck scan https://example.com --format text
```

Run the Mouve ProMax UI:

```sh
npm install
npm run app
```

Open:

```text
http://127.0.0.1:5173/
```

Run the built UI and API together:

```sh
npm run build
npm run preview
```

Open:

```text
http://127.0.0.1:8765/
```

Gate links from a prompt or Markdown file:

```sh
PYTHONPATH=src python3 -m seccheck gate --stdin < message.md
```

Use the helper script:

```sh
./scripts/seccheck-gate --stdin < message.md
```

Exit codes:

- `0`: all scanned links are allowed.
- `2`: at least one link is blocked by the selected gate policy.
- `1`: scanner usage or runtime failure.

## Optional Real Threat-Intel Keys

Set any of these environment variables to enable the corresponding live provider:

```sh
export GOOGLE_SAFE_BROWSING_API_KEY="..."
export VIRUSTOTAL_API_KEY="..."
export PHISHTANK_APP_KEY="..."
```

Then run:

```sh
PYTHONPATH=src python3 -m seccheck scan https://example.com --format json
```

Provider failures are included in the report. They are not converted into clean results.

## Agent Gate Use

`gate` is designed to sit in front of agent browsing or URL ingestion:

```sh
./scripts/seccheck-gate --stdin --format json < incoming_prompt.md
```

The JSON output includes:

- `allowed`: whether every discovered URL passed.
- `blocked_urls`: URLs that failed policy.
- `reports`: full scan reports for auditability.

By default, the harness allows only `safe` verdicts. You can relax this for human-supervised workflows:

```sh
./scripts/seccheck-gate --stdin --allow-verdict caution
```

## Local UI API

The UI calls `POST /api/scan` on the local Node server. The server executes:

```sh
python3 -m seccheck scan <url> --format json
```

It passes arguments with `spawn`, not through a shell string, and treats scanner exit code `2` as a valid unsafe/caution report rather than a server crash.

## Tests

```sh
PYTHONPATH=src python3 -m unittest discover -s tests
npm run build
```

The tests use a real local HTTP server and deterministic local content. They do not mock scanner verdicts or external threat-intel responses.
