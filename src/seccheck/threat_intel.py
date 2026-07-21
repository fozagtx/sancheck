import base64
import json
import os
import urllib.parse
from typing import Any, Dict, List

from .models import Finding, ProviderResult, ScanOptions
from .network import http_json


def check_google_safe_browsing(url: str, options: ScanOptions) -> ProviderResult:
    key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY") or os.getenv("GOOGLE_SAFE_BROWSING_KEY")
    if not key:
        return ProviderResult("google_safe_browsing", "skipped", {"reason": "GOOGLE_SAFE_BROWSING_API_KEY is not set"})
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=%s" % urllib.parse.quote(key)
    payload = {
        "client": {"clientId": "seccheck", "clientVersion": "0.1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    data = http_json(
        endpoint,
        options.timeout,
        method="POST",
        body=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": options.user_agent},
    )
    matches = data.get("matches") or []
    if matches:
        return ProviderResult(
            "google_safe_browsing",
            "match",
            data,
            Finding(
                check="threat_intel",
                severity="critical",
                message="Google Safe Browsing reported this URL as malicious or socially engineered.",
                evidence={"provider": "google_safe_browsing", "matches": matches},
            ),
        )
    return ProviderResult("google_safe_browsing", "clean", data)


def check_virustotal(url: str, options: ScanOptions) -> ProviderResult:
    key = os.getenv("VIRUSTOTAL_API_KEY")
    if not key:
        return ProviderResult("virustotal", "skipped", {"reason": "VIRUSTOTAL_API_KEY is not set"})
    url_id = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    endpoint = "https://www.virustotal.com/api/v3/urls/%s" % url_id
    data = http_json(endpoint, options.timeout, headers={"x-apikey": key, "User-Agent": options.user_agent})
    stats = (((data.get("data") or {}).get("attributes") or {}).get("last_analysis_stats") or {})
    malicious = int(stats.get("malicious") or 0)
    suspicious = int(stats.get("suspicious") or 0)
    if malicious or suspicious:
        severity = "critical" if malicious else "high"
        return ProviderResult(
            "virustotal",
            "match",
            data,
            Finding(
                check="threat_intel",
                severity=severity,
                message="VirusTotal reported malicious or suspicious detections.",
                evidence={"provider": "virustotal", "stats": stats},
            ),
        )
    status = "clean" if data.get("_http_status") == 200 else "error"
    return ProviderResult("virustotal", status, data)


def check_phishtank(url: str, options: ScanOptions) -> ProviderResult:
    key = os.getenv("PHISHTANK_APP_KEY")
    if not key:
        return ProviderResult("phishtank", "skipped", {"reason": "PHISHTANK_APP_KEY is not set"})
    endpoint = "https://checkurl.phishtank.com/checkurl/"
    body = urllib.parse.urlencode({"url": url, "format": "json", "app_key": key}).encode("utf-8")
    data = http_json(
        endpoint,
        options.timeout,
        method="POST",
        body=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": options.user_agent},
    )
    results = data.get("results") or {}
    if results.get("valid") is True and results.get("in_database") is True:
        return ProviderResult(
            "phishtank",
            "match",
            data,
            Finding(
                check="threat_intel",
                severity="critical",
                message="PhishTank reported this URL as a verified phishing URL.",
                evidence={"provider": "phishtank", "results": results},
            ),
        )
    return ProviderResult("phishtank", "clean" if data.get("_http_status") == 200 else "error", data)


def run_threat_intel(url: str, options: ScanOptions) -> List[ProviderResult]:
    if not options.enable_threat_intel:
        return [
            ProviderResult("google_safe_browsing", "skipped", {"reason": "threat intel disabled"}),
            ProviderResult("virustotal", "skipped", {"reason": "threat intel disabled"}),
            ProviderResult("phishtank", "skipped", {"reason": "threat intel disabled"}),
        ]

    results = []
    for provider in (check_google_safe_browsing, check_virustotal, check_phishtank):
        try:
            results.append(provider(url, options))
        except Exception as exc:
            results.append(ProviderResult(provider.__name__.replace("check_", ""), "error", {"error": str(exc), "error_type": exc.__class__.__name__}))
    return results

