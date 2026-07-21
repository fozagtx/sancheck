# seccheck

## Inspiration

Security tools often treat links as simple strings, while agent workflows treat links as instructions, context, and executable next steps. seccheck was inspired by the need for a real preflight gate that checks a URL before an AI-assisted developer workflow opens, summarizes, or acts on it.

## What it does

seccheck scans URLs and returns an agent-safe verdict. It performs live DNS checks, blocks private and reserved network targets by default, validates HTTPS/TLS, follows redirects safely, checks HTTP health, samples page content, detects prompt-injection patterns, looks up domain age through RDAP, and can call real reputation providers when API keys are configured.

It includes both a CLI gate and a local web UI. The CLI can scan direct URLs or extract links from stdin, which makes it useful for prompts, Markdown files, issue text, and other inbound content.

## How we built it

The scanner core is built in Python with the standard library so it can run locally with minimal setup. The pipeline normalizes the URL, resolves DNS, applies SSRF protections, validates TLS, fetches a bounded response sample, analyzes the content for hostile agent instructions, and assembles a weighted findings report.

The UI is built with Vite, React, HeroUI primitives, and the Mouve ProMax theme. A small local Node server exposes `POST /api/scan` and runs the Python scanner with safe argument passing, so the UI shows real scan results rather than mocked data.

## Challenges we ran into

The biggest challenge was keeping the tool honest. Reputation APIs need credentials, so seccheck reports missing providers as skipped instead of pretending a URL is clean.

Another challenge was separating normal web content from prompt-injection content. The scanner handles this by sampling bounded text and HTML, including hidden comments and hidden elements, without executing page scripts.

The UI also needed a pass to feel like a real security tool instead of a flashy demo, so the interface was refined around card primitives, compact wells, and direct scan state.

## Accomplishments that we're proud of

seccheck has a real end-to-end scanner, a CLI gate, a local API bridge, and a usable web interface. It does not depend on mocked safety verdicts, and it preserves provider state clearly when optional API keys are not present.

The scanner also blocks private network targets by default, which matters for agent safety because malicious links can target localhost services, cloud metadata endpoints, or internal network resources.

## What we learned

URL safety for agents is broader than phishing detection. A link can be risky because it resolves to a private address, uses suspicious redirects, has broken TLS, hosts hostile instructions, or tries to smuggle commands into hidden page content.

We also learned that a security UI works better when it prioritizes clear state, evidence, and policy controls over decorative visuals.

## What's next for seccheck

Next steps include browser extension support, CI integration, richer provider adapters, signed scan reports, organization policy profiles, batch scanning, and a review queue for links that need human approval.

