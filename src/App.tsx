import React from "react";
import {
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Chip,
  Input
} from "@heroui/react";

type Severity = "info" | "low" | "medium" | "high" | "critical";
type Verdict = "safe" | "caution" | "unsafe";
type ThemeId = "default" | "brutalism" | "glass" | "mouve";
type ChipColor = "accent" | "danger" | "default" | "success" | "warning";

type Finding = {
  check: string;
  severity: Severity;
  message: string;
  weight: number;
  evidence?: Record<string, unknown>;
};

type ProviderResult = {
  provider: string;
  status: string;
  data?: Record<string, unknown>;
  finding?: Finding;
};

type ScanReport = {
  original_url: string;
  normalized_url: string | null;
  final_url: string | null;
  checked_at: string;
  verdict: Verdict;
  safety_score: number;
  risk_score: number;
  allowed_for_agent: boolean;
  findings: Finding[];
  redirects: Array<Record<string, unknown>>;
  checks: Record<string, unknown>;
  provider_results: ProviderResult[];
  error?: string | null;
};

type ScanOptions = {
  allowPrivate: boolean;
  threatIntel: boolean;
  domainAge: boolean;
};

const THEMES: Array<{ id: ThemeId; label: string }> = [
  { id: "default", label: "Default" },
  { id: "brutalism", label: "Brutalism" },
  { id: "glass", label: "Glass" },
  { id: "mouve", label: "Mouve" }
];

const EXAMPLES = [
  "https://example.com",
  "https://example.org"
];

function App() {
  const [theme, setTheme] = React.useState<ThemeId>("mouve");
  const [url, setUrl] = React.useState(EXAMPLES[0]);
  const [options, setOptions] = React.useState<ScanOptions>({
    allowPrivate: false,
    threatIntel: true,
    domainAge: true
  });
  const [report, setReport] = React.useState<ScanReport | null>(null);
  const [isScanning, setIsScanning] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    document.documentElement.dataset.theme = `${theme}-light`;
  }, [theme]);

  async function handleScan(event?: React.FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const nextUrl = url.trim();

    if (!nextUrl) {
      setError("Enter a URL.");
      return;
    }

    setIsScanning(true);
    setError(null);

    try {
      const response = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: nextUrl, options })
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Scan failed.");
      }

      setReport(payload.report);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Scan failed.");
    } finally {
      setIsScanning(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="product-frame">
        <TopBar theme={theme} setTheme={setTheme} />

        <div className="page-head">
          <div>
            <p className="eyebrow">seccheck</p>
            <h1>URL scan console</h1>
            <p>Run a live gate before a link enters an agent workflow.</p>
          </div>
          <Chip color={report ? gateColor(report.verdict, report.allowed_for_agent) : "default"} variant="soft">
            {isScanning ? "Scanning" : report ? gateLabel(report) : "No verdict"}
          </Chip>
        </div>

        <section className="console-grid" aria-label="scan console">
          <ScanCard
            url={url}
            setUrl={setUrl}
            isScanning={isScanning}
            onScan={handleScan}
          />
          <PolicyCard
            options={options}
            setOptions={setOptions}
            report={report}
          />
        </section>

        {error ? <ErrorCard message={error} /> : null}

        <GateDecision report={report} isScanning={isScanning} />

        {report ? (
          <section className="report-grid" aria-label="scan report">
            <ReportSummary report={report} />
            <TransportCard report={report} />
            <ContentCard report={report} />
            <ReputationCard report={report} />
            <FindingsCard findings={report.findings.filter((finding) => finding.severity !== "info")} />
          </section>
        ) : (
          <EmptyReport />
        )}
      </section>
    </main>
  );
}

function TopBar({
  theme,
  setTheme
}: {
  theme: ThemeId;
  setTheme: React.Dispatch<React.SetStateAction<ThemeId>>;
}) {
  return (
    <Card className="topbar">
      <CardContent>
        <div className="brand-lockup">
          <img className="brand-logo" src="/logo.png" alt="seccheck logo" />
        </div>
        <div className="theme-switcher" aria-label="theme">
          {THEMES.map((item) => (
            <Button
              key={item.id}
              className="theme-button"
              isIconOnly
              size="sm"
              variant={theme === item.id ? "primary" : "outline"}
              aria-label={item.label}
              onPress={() => setTheme(item.id)}
            >
              <span className={`theme-dot theme-dot-${item.id}`} />
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ScanCard({
  url,
  setUrl,
  isScanning,
  onScan
}: {
  url: string;
  setUrl: React.Dispatch<React.SetStateAction<string>>;
  isScanning: boolean;
  onScan: (event?: React.FormEvent<HTMLFormElement>) => Promise<void>;
}) {
  return (
    <Card className="scan-card">
      <CardHeader className="card-heading">
        <div>
          <CardTitle>Scan</CardTitle>
          <CardDescription>DNS, TLS, redirects, page content, and optional reputation checks.</CardDescription>
        </div>
        <Button className="pill-button" size="sm" variant="outline" onPress={() => void onScan()} isDisabled={isScanning}>
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        <form className="scan-form" onSubmit={onScan}>
          <label className="url-field">
            <span>URL</span>
            <div className="url-input-wrap">
              <Input
                aria-label="URL"
                className="url-input"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example.com"
              />
            </div>
          </label>
          <Button className="scan-button pill-button" variant="primary" type="submit" isDisabled={isScanning}>
            {isScanning ? "Scanning" : "Scan link"}
          </Button>
        </form>

        <div className="quick-row">
          {EXAMPLES.map((example) => (
            <Button key={example} className="pill-button" size="sm" variant="outline" onPress={() => setUrl(example)}>
              {new URL(example).hostname}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function PolicyCard({
  options,
  setOptions,
  report
}: {
  options: ScanOptions;
  setOptions: React.Dispatch<React.SetStateAction<ScanOptions>>;
  report: ScanReport | null;
}) {
  return (
    <Card className="policy-card">
      <CardHeader>
        <CardTitle>Policy</CardTitle>
        <CardDescription>Controls for this scan only. Provider results stay honest when keys are missing.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="toggle-stack">
          <Toggle
            label="Threat intel"
            detail="Use configured provider keys"
            checked={options.threatIntel}
            onChange={(threatIntel) => setOptions((current) => ({ ...current, threatIntel }))}
          />
          <Toggle
            label="Domain age"
            detail="RDAP lookup when available"
            checked={options.domainAge}
            onChange={(domainAge) => setOptions((current) => ({ ...current, domainAge }))}
          />
          <Toggle
            label="Allow private targets"
            detail="Off blocks loopback and internal IPs"
            checked={options.allowPrivate}
            tone="warning"
            onChange={(allowPrivate) => setOptions((current) => ({ ...current, allowPrivate }))}
          />
        </div>
        <div className="provider-strip">
          {providerStatuses(report).map((provider) => (
            <Chip key={provider.label} size="sm" color={providerTone(provider.status)} variant="soft">
              {provider.label}: {provider.status}
            </Chip>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function GateDecision({ report, isScanning }: { report: ScanReport | null; isScanning: boolean }) {
  const status = isScanning ? "Checking" : report ? gateTitle(report) : "Waiting";

  return (
    <Card className={`decision-card ${report?.verdict ? `gate-${report.verdict}` : ""}`}>
      <CardContent>
        <div>
          <span className="label">Gate decision</span>
          <strong>{status}</strong>
          <p>{gateCopy(report, isScanning)}</p>
        </div>
        <div className="decision-metrics">
          <MetricWell label="Safety" value={report ? `${report.safety_score}/10` : "Pending"} />
          <MetricWell label="Risk" value={report ? `${report.risk_score}/100` : "Pending"} />
          <MetricWell label="Agent policy" value={report ? (report.allowed_for_agent ? "Allow" : "Block") : "Pending"} />
        </div>
      </CardContent>
    </Card>
  );
}

function ReportSummary({ report }: { report: ScanReport }) {
  return (
    <Card className="report-card summary-card">
      <CardHeader className="card-heading">
        <div>
          <CardTitle>Verdict</CardTitle>
          <CardDescription>{report.final_url || report.normalized_url}</CardDescription>
        </div>
        <Chip color={verdictColor(report.verdict)} variant="soft">
          {report.verdict}
        </Chip>
      </CardHeader>
      <CardContent>
        <div className="metric-grid">
          <MetricWell label="Safety score" value={`${report.safety_score}/10`} />
          <MetricWell label="Risk score" value={`${report.risk_score}/100`} />
        </div>
        <div className={`score-track score-track-${report.verdict}`} aria-label="Safety score">
          <span style={{ width: `${report.safety_score * 10}%` }} />
        </div>
      </CardContent>
    </Card>
  );
}

function TransportCard({ report }: { report: ScanReport }) {
  const http = report.checks.http as { status?: number; reason?: string } | undefined;
  const dns = report.checks.dns as { addresses?: string[] } | undefined;
  const tls = report.checks.tls as { valid?: boolean; days_until_expiry?: number; status?: string } | undefined;

  return (
    <Card className="report-card">
      <CardHeader>
        <CardTitle>Transport</CardTitle>
        <CardDescription>Connection evidence from the live request.</CardDescription>
      </CardHeader>
      <CardContent className="check-list">
        <CheckRow label="HTTP" value={http?.status ? `${http.status} ${http.reason || ""}`.trim() : "n/a"} />
        <CheckRow label="DNS" value={dns?.addresses?.length ? `${dns.addresses.length} address${dns.addresses.length > 1 ? "es" : ""}` : "n/a"} />
        <CheckRow label="TLS" value={tls?.valid ? `${tls.days_until_expiry ?? "valid"} days` : tls?.status || "n/a"} />
        <CheckRow label="Redirects" value={`${report.redirects.length}`} />
      </CardContent>
    </Card>
  );
}

function ContentCard({ report }: { report: ScanReport }) {
  const prompt = report.checks.prompt_injection as { score?: number; severity?: string; status?: string } | undefined;
  const http = report.checks.http as { content_type?: string; sample_bytes?: number; truncated?: boolean } | undefined;

  return (
    <Card className="report-card">
      <CardHeader>
        <CardTitle>Content</CardTitle>
        <CardDescription>Bounded sample review for prompt-injection patterns.</CardDescription>
      </CardHeader>
      <CardContent className="check-list">
        <CheckRow label="Prompt score" value={typeof prompt?.score === "number" ? `${prompt.score}/100` : prompt?.status || "n/a"} />
        <CheckRow label="Severity" value={prompt?.severity || "n/a"} />
        <CheckRow label="Type" value={http?.content_type || "n/a"} />
        <CheckRow label="Sample" value={typeof http?.sample_bytes === "number" ? `${http.sample_bytes} bytes${http.truncated ? " sampled" : ""}` : "n/a"} />
      </CardContent>
    </Card>
  );
}

function ReputationCard({ report }: { report: ScanReport }) {
  return (
    <Card className="report-card">
      <CardHeader>
        <CardTitle>Reputation</CardTitle>
        <CardDescription>Live provider status. Skipped means no key or disabled check.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="provider-grid">
          {providerStatuses(report).map((provider) => (
            <div className="provider-well" key={provider.label}>
              <span>{provider.label}</span>
              <Chip size="sm" color={providerTone(provider.status)} variant="soft">
                {provider.status}
              </Chip>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function FindingsCard({ findings }: { findings: Finding[] }) {
  const sorted = [...findings].sort((left, right) => right.weight - left.weight);

  return (
    <Card className="report-card findings-card">
      <CardHeader>
        <CardTitle>Findings</CardTitle>
        <CardDescription>{sorted.length ? "Highest weighted signals." : "No blocking signals."}</CardDescription>
      </CardHeader>
      <CardContent>
        {sorted.length ? (
          <div className="finding-list">
            {sorted.map((finding) => (
              <article className="finding-row" key={`${finding.check}-${finding.message}`}>
                <span className={`severity-dot severity-${finding.severity}`} />
                <div>
                  <p>
                    <span>{finding.check}</span>
                    <Chip size="sm" variant="soft" color={severityColor(finding.severity)}>
                      {finding.severity}
                    </Chip>
                  </p>
                  <small>{finding.message}</small>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="quiet-state">
            <p>Clean scan.</p>
            <span>The strict gate did not find anything blocking.</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyReport() {
  return (
    <Card className="empty-card">
      <CardContent>
        <p>No report yet.</p>
        <span>Run a scan to populate DNS, TLS, content, reputation, and findings.</span>
      </CardContent>
    </Card>
  );
}

function Toggle({
  label,
  detail,
  checked,
  tone,
  onChange
}: {
  label: string;
  detail: string;
  checked: boolean;
  tone?: "warning";
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className={`toggle ${tone === "warning" ? "toggle-warning" : ""}`}>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span aria-hidden="true" />
      <div>
        <strong>{label}</strong>
        <small>{detail}</small>
      </div>
    </label>
  );
}

function MetricWell({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-well">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function CheckRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="check-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ErrorCard({ message }: { message: string }) {
  return (
    <Card className="error-card">
      <CardContent>
        <p>{message}</p>
      </CardContent>
    </Card>
  );
}

function providerStatuses(report: ScanReport | null) {
  if (!report) {
    return [
      { label: "Safe Browsing", status: "pending" },
      { label: "VirusTotal", status: "pending" },
      { label: "PhishTank", status: "pending" }
    ];
  }

  return report.provider_results.map((provider) => ({
    label: provider.provider.replace("google_safe_browsing", "Safe Browsing").replace("virustotal", "VirusTotal").replace("phishtank", "PhishTank"),
    status: provider.status
  }));
}

function gateTitle(report: ScanReport) {
  if (report.allowed_for_agent) return "Allowed";
  return "Blocked";
}

function gateCopy(report: ScanReport | null, isScanning: boolean) {
  if (isScanning) return "Resolving host, validating transport, and sampling content.";
  if (!report) return "No URL has been checked in this session.";
  if (report.allowed_for_agent) return "The link passed the strict agent policy.";
  return "The link failed the strict agent policy. Review findings before opening manually.";
}

function gateLabel(report: ScanReport) {
  return report.allowed_for_agent ? "Allow" : "Block";
}

function verdictColor(verdict: Verdict): ChipColor {
  if (verdict === "safe") return "success";
  if (verdict === "caution") return "warning";
  return "danger";
}

function gateColor(verdict?: Verdict, allowed?: boolean): ChipColor {
  if (allowed) return "success";
  if (verdict === "unsafe") return "danger";
  if (verdict === "caution") return "warning";
  return "default";
}

function severityColor(severity: Severity): ChipColor {
  if (severity === "critical" || severity === "high") return "danger";
  if (severity === "medium") return "warning";
  return "default";
}

function providerTone(status: string): ChipColor {
  if (status === "match") return "danger";
  if (status === "clean") return "success";
  if (status === "error") return "warning";
  return "default";
}

export default App;
