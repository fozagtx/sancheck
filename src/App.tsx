import { Button, Card, CardContent, CardDescription, CardHeader, CardTitle, Chip } from "@heroui/react";

const COMMANDS = [
  {
    title: "Middleware",
    command: "printf 'check https://example.com' | ./scripts/seccheck-gate"
  },
  {
    title: "Direct scan",
    command: "PYTHONPATH=src python3 -m seccheck scan https://example.com --format json"
  },
  {
    title: "Text gate",
    command: "PYTHONPATH=src python3 -m seccheck gate --stdin --format json < message.md"
  }
];

const CHECKS = [
  "DNS resolution and private-address blocking",
  "HTTPS certificate validation",
  "Redirect and HTTP response checks",
  "Bounded page-content sampling",
  "Prompt-injection pattern detection",
  "Optional live provider lookups"
];

const FEATURES = [
  {
    title: "Codex Plugin",
    description: "Drop-in plugin for Codex agent workflows. Gate URLs before opening them.",
    icon: "🔌"
  },
  {
    title: "URL Gate",
    description: "Extract and validate URLs from any text or JSON payload.",
    icon: "🚪"
  },
  {
    title: "Prompt Injection",
    description: "Detect hidden instructions in fetched page content.",
    icon: "🛡️"
  },
  {
    title: "Middleware Contract",
    description: "stdin in, JSON decision out. Exit codes for CI/CD.",
    icon: "📋"
  }
];

function App() {
  return (
    <main className="landing-shell">
      <section className="landing-frame">
        <header className="topbar">
          <img className="brand-logo" src="/logo.png" alt="seccheck logo" />
        </header>

        <section className="hero-section">
          <div>
            <p className="eyebrow">seccheck</p>
            <h1>URL safety middleware for agent workflows.</h1>
            <div className="hero-actions">
              <Button className="pill-button" variant="primary" onPress={() => copyText(COMMANDS[0].command)}>
                Copy gate command
              </Button>
              <a
                href="https://github.com/fozagtx/seccheck"
                target="_blank"
                rel="noopener noreferrer"
                className="pill-button get-started-link"
              >
                View on GitHub
              </a>
            </div>
          </div>
          <Card className="contract-card">
            <CardHeader>
              <CardTitle>Middleware contract</CardTitle>
              <CardDescription>Plain text or JSON in. JSON decision out.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="contract-row">
                <span>Allow</span>
                <strong>exit 0</strong>
              </div>
              <div className="contract-row">
                <span>Block</span>
                <strong>exit 2</strong>
              </div>
              <div className="contract-row">
                <span>Failure</span>
                <strong>exit 1</strong>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="feature-grid" aria-label="features">
          {FEATURES.map((feature) => (
            <Card className="feature-card" key={feature.title}>
              <CardContent>
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="command-grid" aria-label="commands">
          {COMMANDS.map((item) => (
            <Card className="command-card" key={item.title}>
              <CardHeader>
                <CardTitle>{item.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <code>{item.command}</code>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="content-grid">
          <Card>
            <CardHeader>
              <CardTitle>What it checks</CardTitle>
              <CardDescription>No mock verdicts. Missing provider keys are shown as skipped.</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="check-list">
                {CHECKS.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Agent output</CardTitle>
              <CardDescription>The wrapper returns a stable decision payload.</CardDescription>
            </CardHeader>
            <CardContent>
              <pre>{`{
  "tool": "seccheck",
  "mode": "middleware",
  "decision": "allow",
  "allowed": true,
  "blocked_urls": []
}`}</pre>
            </CardContent>
          </Card>
        </section>

        <footer className="landing-footer">
          <p>
            <a href="https://github.com/fozagtx/seccheck" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </footer>
      </section>
    </main>
  );
}

function copyText(value: string) {
  void navigator.clipboard?.writeText(value);
}

export default App;
