# Codex usage

Session: `019f8658-5272-7480-ae44-3a4ebd620ba2`

Built most of the scanner core with Codex (GPT-5.6):

- URL validation / normalization
- DNS + SSRF protection
- TLS cert checks
- HTTP client + redirect handling
- Prompt injection detection
- Threat intel (Safe Browsing, VirusTotal, PhishTank)
- CLI + middleware interface

Workflow was: describe what I needed → Codex drafts it → I test → fix → next piece.

Codex got these right without much fuss:
- Blocking private IPs on DNS resolve
- Cert expiration checks
- Safe redirect following
- Prompt injection pattern matching

I had to clean up:
- URL normalization edge cases
- Network timeout error handling
- Tests for specific attack patterns

Decisions made in those sessions:
- Stdlib only (no third-party deps)
- Middleware: stdin in, JSON out, exit codes
- Weighted findings for risk scoring
- Missing API keys reported as "skipped", not hidden

Order of work:
1. Scaffold
2. Core modules (`url_utils`, `network`, `models`, `scanner`)
3. Prompt injection
4. Threat intel providers
5. CLI
6. Tests
7. Packaged as a Codex plugin

Roughly 15-20 hours saved. Scanner core is ~2000 lines of Python. Codex did the boilerplate; I spent time on the security logic and edge cases.
