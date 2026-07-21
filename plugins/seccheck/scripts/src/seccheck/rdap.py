import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from .models import Finding, ScanOptions
from .network import http_json
from .url_utils import parent_domains


BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
_BOOTSTRAP_CACHE: Dict[str, Any] = {"loaded_at": 0.0, "services": []}


def _load_bootstrap(options: ScanOptions) -> List[Any]:
    now = time.time()
    if _BOOTSTRAP_CACHE["services"] and now - _BOOTSTRAP_CACHE["loaded_at"] < 86400:
        return _BOOTSTRAP_CACHE["services"]
    data = http_json(BOOTSTRAP_URL, options.timeout, headers={"User-Agent": options.user_agent})
    services = data.get("services") or []
    _BOOTSTRAP_CACHE["loaded_at"] = now
    _BOOTSTRAP_CACHE["services"] = services
    return services


def _rdap_base_for_tld(tld: str, options: ScanOptions) -> Optional[str]:
    for service in _load_bootstrap(options):
        tlds = [item.lower() for item in (service[0] or [])]
        urls = service[1] or []
        if tld.lower() in tlds and urls:
            return urls[0]
    return None


def _event_date(data: Dict[str, Any]) -> Optional[str]:
    for event in data.get("events") or []:
        action = (event.get("eventAction") or "").lower()
        if action in ("registration", "domain registration", "registered"):
            return event.get("eventDate")
    for event in data.get("events") or []:
        action = (event.get("eventAction") or "").lower()
        if "registration" in action:
            return event.get("eventDate")
    return None


def check_domain_age(host: str, options: ScanOptions) -> Tuple[Dict[str, Any], List[Finding]]:
    findings: List[Finding] = []
    data: Dict[str, Any] = {"host": host, "status": "skipped"}
    if not options.check_domain_age:
        data["reason"] = "domain age check disabled"
        return data, findings

    candidates = list(parent_domains(host))
    if not candidates:
        data["reason"] = "host has no registrable parent domain candidate"
        return data, findings

    last_error = None
    for domain in candidates:
        tld = domain.rsplit(".", 1)[-1].lower()
        try:
            base = _rdap_base_for_tld(tld, options)
            if not base:
                continue
            url = base.rstrip("/") + "/domain/" + quote(domain.upper())
            response = http_json(url, options.timeout, headers={"User-Agent": options.user_agent})
            if response.get("_http_status") != 200:
                last_error = {"domain": domain, "status": response.get("_http_status")}
                continue
            registered_at = _event_date(response)
            data = {
                "host": host,
                "domain": domain,
                "status": "found",
                "registered_at": registered_at,
                "rdap_status": response.get("status"),
            }
            if registered_at:
                registered = datetime.fromisoformat(registered_at.replace("Z", "+00:00")).replace(tzinfo=None)
                age_days = (datetime.utcnow() - registered).days
                data["age_days"] = age_days
                if age_days < 0:
                    findings.append(Finding(check="domain_age", severity="medium", message="RDAP registration date is in the future.", evidence=data))
                elif age_days < 30:
                    findings.append(Finding(check="domain_age", severity="high", message="Domain appears to be newly registered.", evidence=data))
                elif age_days < 90:
                    findings.append(Finding(check="domain_age", severity="medium", message="Domain is relatively new.", evidence=data))
            return data, findings
        except Exception as exc:
            last_error = {"domain": domain, "error": str(exc), "error_type": exc.__class__.__name__}
            continue

    data["status"] = "error"
    data["last_error"] = last_error
    return data, findings

