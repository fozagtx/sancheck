# sancheck

## Inspiration

Security tools often treat links as simple strings, while agent workflows treat links as context and next steps. sancheck was inspired by the need for a real preflight gate that checks a URL before a developer workflow opens, summarizes, or acts on it.

## What it does

sancheck scans URLs and returns a machine-readable allow or block decision. It performs live DNS checks, blocks private and reserved network targets by default, validates HTTPS/TLS, follows redirects safely, checks HTTP health, samples page content, detects prompt-injection patterns, looks up domain age through RDAP, and can call real reputation providers when API keys are configured.

It includes a CLI gate, a middleware command, and a bundled Codex plugin package. The middleware reads plain text or JSON from stdin, extracts URLs, scans them, prints a JSON decision payload, and exits with `2` when a link is blocked.

## How we built it

The scanner core is built in Python with the standard library so it can run locally with minimal setup. The pipeline normalizes the URL, resolves DNS, applies SSRF protections, validates TLS, fetches a bounded response sample, analyzes the content for hostile agent instructions, and assembles a weighted findings report.

The plugin bundles the scanner source with a small shell wrapper and a skill file that tells agents when to gate links. The web surface is a static Vite and React landing page built with HeroUI primitives, using the generated sancheck logo and favicon assets.

## Challenges we ran into

The biggest challenge was keeping the tool honest. Reputation APIs need credentials, so sancheck reports missing providers as skipped instead of pretending a URL is clean.

Another challenge was separating normal web content from prompt-injection content. The scanner handles this by sampling bounded text and HTML, including hidden comments and hidden elements, without executing page scripts.

Packaging the tool as a plugin also required a clear middleware contract: stdin text or JSON in, JSON decision out, exit `2` on block.

## Accomplishments that we're proud of

sancheck has a real end-to-end scanner, a CLI gate, middleware output, and a bundled plugin package. It does not depend on mocked safety verdicts, and it preserves provider state clearly when optional API keys are not present.

The scanner also blocks private network targets by default, which matters for agent safety because malicious links can target localhost services, cloud metadata endpoints, or internal network resources.

## What we learned

URL safety for agents is broader than phishing detection. A link can be risky because it resolves to a private address, uses suspicious redirects, has broken TLS, hosts hostile instructions, or tries to smuggle commands into hidden page content.

We also learned that a security tool works better when it prioritizes clear state, evidence, and policy over decorative visuals.

## What's next for sancheck

Next steps include CI integration, richer provider adapters, signed scan reports, organization policy profiles, batch scanning, and a review queue for links that need human approval.
