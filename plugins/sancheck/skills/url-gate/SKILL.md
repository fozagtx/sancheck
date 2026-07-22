---
name: sancheck-url-gate
description: Gate URLs with the bundled sancheck scanner before an agent opens, fetches, summarizes, or acts on untrusted links.
---

# sancheck URL Gate

**API keys for testing:** [testing keys](https://docs.google.com/document/d/1Ga4IVy5-57BDiO3-JpJu5cgq1fnJpm1Vb943fnYOWB0/edit?usp=sharing)

Use this skill whenever a task includes external links or asks you to open, fetch, summarize, inspect, crawl, or act on an untrusted URL.

## Workflow

1. Resolve the plugin root as the directory two levels above this `SKILL.md`.
2. Send the untrusted text, prompt, JSON payload, or URL list to `scripts/sancheck-gate`.
3. Continue only when the command exits `0` and the JSON payload has `"allowed": true`.
4. If the command exits `2`, do not open blocked URLs. Report the blocked URLs and the highest-signal findings.
5. If the command exits `1`, treat the gate as failed closed and ask for user direction before using the URL.

## Command

```sh
printf '%s\n' "$UNTRUSTED_TEXT_OR_JSON" | "$PLUGIN_ROOT/scripts/sancheck-gate"
```

Direct URL form:

```sh
"$PLUGIN_ROOT/scripts/sancheck-gate" https://example.com
```

The gate emits JSON with `decision`, `allowed`, `blocked_urls`, and full `reports`. Exit code `2` means at least one URL failed policy.

## Provider Keys

```sh
GOOGLE_SAFE_BROWSING_API_KEY
VIRUSTOTAL_API_KEY
PHISHTANK_APP_KEY
```

Missing keys show as skipped, not as clean results.
