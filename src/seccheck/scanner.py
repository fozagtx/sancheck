from datetime import datetime
from typing import List, Optional
from urllib.parse import urlsplit

from .heuristics import summarize_findings, url_heuristics
from .models import Finding, ScanOptions, ScanReport
from .network import fetch_url, hostname_port, resolve_host, validate_tls
from .prompt_injection import analyze_prompt_injection, finding_from_prompt_report
from .rdap import check_domain_age
from .threat_intel import run_threat_intel
from .url_utils import UrlError, normalize_url, split_url


def _risk_score(findings: List[Finding]) -> int:
    return min(100, sum(max(0, finding.risk_weight()) for finding in findings))


def _verdict(findings: List[Finding], risk_score: int) -> str:
    if any(finding.severity == "critical" for finding in findings) or risk_score >= 60:
        return "unsafe"
    if risk_score >= 25 or any(finding.severity == "high" for finding in findings):
        return "caution"
    return "safe"


def _safety_score(risk_score: int) -> int:
    return max(1, min(10, 10 - ((risk_score + 9) // 10)))


def _agent_allowed(verdict: str, findings: List[Finding]) -> bool:
    if verdict != "safe":
        return False
    for finding in findings:
        if finding.check in ("prompt_injection", "dns", "tls", "threat_intel") and finding.severity in ("high", "critical"):
            return False
    return True


def _empty_report(original_url: str, normalized_url: Optional[str], findings: List[Finding], error: Optional[str] = None) -> ScanReport:
    risk = _risk_score(findings)
    verdict = _verdict(findings, risk)
    return ScanReport(
        original_url=original_url,
        normalized_url=normalized_url,
        final_url=None,
        checked_at=datetime.utcnow(),
        verdict=verdict,
        safety_score=_safety_score(risk),
        risk_score=risk,
        allowed_for_agent=False,
        findings=findings,
        checks={"summary": summarize_findings(findings)},
        error=error,
    )


def scan_url(raw_url: str, options: Optional[ScanOptions] = None) -> ScanReport:
    options = options or ScanOptions()
    findings: List[Finding] = []
    provider_results = []
    checks = {}

    try:
        normalized = normalize_url(raw_url)
    except (UrlError, ValueError) as exc:
        findings.append(Finding(check="url", severity="critical", message=str(exc), evidence={"input": raw_url}))
        return _empty_report(raw_url, None, findings, error=str(exc))

    findings.extend(url_heuristics(raw_url, normalized))
    parsed = split_url(normalized)
    host, port = hostname_port(parsed)

    addresses, dns_findings = resolve_host(host, port, options.timeout, options.allow_private)
    checks["dns"] = {"host": host, "port": port, "addresses": addresses}
    findings.extend(dns_findings)
    blocked_private = any(finding.severity == "critical" and finding.check == "dns" for finding in dns_findings)

    if parsed.scheme == "https" and not (blocked_private and not options.allow_private):
        tls_data, tls_findings = validate_tls(host, port, options.timeout)
        checks["tls"] = tls_data
        findings.extend(tls_findings)
    elif parsed.scheme == "https":
        checks["tls"] = {"status": "skipped", "reason": "blocked before TLS due to non-public DNS target"}

    if not blocked_private or options.allow_private:
        rdap_data, rdap_findings = check_domain_age(host, options)
        checks["domain_age"] = rdap_data
        findings.extend(rdap_findings)
    else:
        checks["domain_age"] = {"status": "skipped", "reason": "blocked before RDAP due to non-public DNS target"}

    http_data, http_findings, redirects, content = fetch_url(normalized, options)
    checks["http"] = http_data
    findings.extend(http_findings)

    final_url = http_data.get("url") or normalized
    final_content_type = http_data.get("content_type") or ""

    if content and _is_prompt_scannable(final_content_type):
        prompt_report = analyze_prompt_injection(content, final_content_type)
        checks["prompt_injection"] = prompt_report.to_dict()
        prompt_finding = finding_from_prompt_report(prompt_report)
        if prompt_finding.severity != "info":
            findings.append(prompt_finding)
    else:
        checks["prompt_injection"] = {
            "status": "skipped",
            "reason": "no scannable text content fetched",
            "content_type": final_content_type,
        }

    if redirects:
        findings.append(
            Finding(
                check="http",
                severity="low" if len(redirects) <= 2 else "medium",
                message="URL redirects before reaching the final target.",
                evidence={"redirects": redirects},
            )
        )

    provider_results = run_threat_intel(final_url, options)
    for result in provider_results:
        if result.finding:
            findings.append(result.finding)

    risk = _risk_score(findings)
    verdict = _verdict(findings, risk)
    allowed = _agent_allowed(verdict, findings)
    checks["summary"] = summarize_findings(findings)

    return ScanReport(
        original_url=raw_url,
        normalized_url=normalized,
        final_url=final_url,
        checked_at=datetime.utcnow(),
        verdict=verdict,
        safety_score=_safety_score(risk),
        risk_score=risk,
        allowed_for_agent=allowed,
        findings=findings,
        redirects=redirects,
        checks=checks,
        provider_results=provider_results,
    )


def _is_prompt_scannable(content_type: str) -> bool:
    lowered = content_type.lower()
    if not lowered:
        return True
    return any(token in lowered for token in ("text/", "html", "json", "xml", "markdown", "javascript"))
