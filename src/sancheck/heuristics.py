import ipaddress
import math
import re
from typing import Any, Dict, List
from urllib.parse import unquote, urlsplit

from .models import Finding


def _non_public_ip_literal(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "buff.ly",
    "cutt.ly",
    "is.gd",
    "s.id",
    "rebrand.ly",
    "shorturl.at",
}

SUSPICIOUS_TLDS = {
    "zip",
    "mov",
    "click",
    "country",
    "download",
    "fit",
    "gq",
    "kim",
    "loan",
    "men",
    "party",
    "review",
    "stream",
    "tk",
    "top",
    "work",
    "xyz",
}

BRAND_LURE_WORDS = {
    "account",
    "admin",
    "bank",
    "billing",
    "confirm",
    "credential",
    "login",
    "password",
    "pay",
    "secure",
    "signin",
    "sso",
    "update",
    "verify",
    "wallet",
}


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    entropy = 0.0
    for count in counts.values():
        probability = count / float(len(value))
        entropy -= probability * math.log(probability, 2)
    return entropy


def url_heuristics(raw_url: str, normalized_url: str, allow_private: bool = False) -> List[Finding]:
    parsed = urlsplit(normalized_url)
    findings: List[Finding] = []
    host = parsed.hostname or ""
    tld = host.rsplit(".", 1)[-1].lower() if "." in host else ""
    decoded_path = unquote(parsed.path + ("?" + parsed.query if parsed.query else ""))
    host_tokens = set(re.split(r"[^a-z0-9]+", host.lower()))
    path_tokens = set(re.split(r"[^a-z0-9]+", decoded_path.lower()))
    private_literal = allow_private and _non_public_ip_literal(host)

    if parsed.scheme != "https":
        if private_literal:
            findings.append(
                Finding(
                    check="url",
                    severity="info",
                    message="URL does not use HTTPS on an explicitly allowed private target.",
                    weight=0,
                    evidence={"scheme": parsed.scheme},
                )
            )
        else:
            findings.append(Finding(check="url", severity="medium", message="URL does not use HTTPS.", evidence={"scheme": parsed.scheme}))
    if "@" in urlsplit(raw_url if "://" in raw_url else "https://" + raw_url).netloc:
        findings.append(Finding(check="url", severity="high", message="URL contains userinfo/@ syntax that can hide the real host."))
    if host.startswith("xn--") or ".xn--" in host:
        findings.append(Finding(check="url", severity="medium", message="Hostname uses punycode; inspect for lookalike characters.", evidence={"host": host}))
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", host):
        if private_literal:
            findings.append(
                Finding(
                    check="url",
                    severity="info",
                    message="URL uses a private/loopback IPv4 literal and private targets are explicitly allowed.",
                    weight=0,
                    evidence={"host": host},
                )
            )
        else:
            findings.append(Finding(check="url", severity="medium", message="URL uses an IPv4 literal instead of a domain.", evidence={"host": host}))
    if parsed.port and parsed.port not in (80, 443):
        if private_literal:
            findings.append(
                Finding(
                    check="url",
                    severity="info",
                    message="URL uses a non-standard port on an explicitly allowed private target.",
                    weight=0,
                    evidence={"port": parsed.port},
                )
            )
        else:
            findings.append(Finding(check="url", severity="medium", message="URL uses an uncommon port.", evidence={"port": parsed.port}))
    if host in SHORTENERS:
        findings.append(Finding(check="url", severity="medium", message="URL uses a public link shortener.", evidence={"host": host}))
    if tld in SUSPICIOUS_TLDS:
        findings.append(Finding(check="url", severity="low", message="URL uses a TLD commonly abused in phishing campaigns.", evidence={"tld": tld}))
    lure_words = sorted((host_tokens | path_tokens) & BRAND_LURE_WORDS)
    if len(lure_words) >= 2:
        findings.append(Finding(check="url", severity="medium", message="URL contains multiple credential/payment lure words.", evidence={"words": lure_words}))
    if len(host) > 60:
        findings.append(Finding(check="url", severity="low", message="Hostname is unusually long.", evidence={"host_length": len(host)}))
    if len(decoded_path) > 140:
        findings.append(Finding(check="url", severity="low", message="Path/query is unusually long.", evidence={"path_query_length": len(decoded_path)}))
    if _entropy(host.replace(".", "")) > 4.0 and len(host) > 24:
        findings.append(Finding(check="url", severity="medium", message="Hostname has high entropy and may be generated.", evidence={"host": host}))
    if "%00" in raw_url.lower() or "\\x00" in raw_url.lower():
        findings.append(Finding(check="url", severity="high", message="URL contains null-byte encoding."))
    return findings


def summarize_findings(findings: List[Finding]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    return {"count": len(findings), "by_severity": counts}

