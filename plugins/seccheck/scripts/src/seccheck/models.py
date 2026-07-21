from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


SEVERITY_WEIGHTS = {
    "info": 0,
    "low": 5,
    "medium": 15,
    "high": 30,
    "critical": 45,
}


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    weight: Optional[int] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    def risk_weight(self) -> int:
        if self.weight is not None:
            return self.weight
        return SEVERITY_WEIGHTS.get(self.severity, 0)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
            "weight": self.risk_weight(),
        }
        if self.evidence:
            payload["evidence"] = self.evidence
        return payload


@dataclass
class ProviderResult:
    provider: str
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    finding: Optional[Finding] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "provider": self.provider,
            "status": self.status,
            "data": self.data,
        }
        if self.finding:
            payload["finding"] = self.finding.to_dict()
        return payload


@dataclass
class ScanOptions:
    timeout: float = 5.0
    max_redirects: int = 5
    max_bytes: int = 65536
    allow_private: bool = False
    verify_tls: bool = True
    enable_threat_intel: bool = True
    check_domain_age: bool = True
    user_agent: str = "seccheck/0.1 link-safety-harness"


@dataclass
class ScanReport:
    original_url: str
    normalized_url: Optional[str]
    final_url: Optional[str]
    checked_at: datetime
    verdict: str
    safety_score: int
    risk_score: int
    allowed_for_agent: bool
    findings: List[Finding] = field(default_factory=list)
    redirects: List[Dict[str, Any]] = field(default_factory=list)
    checks: Dict[str, Any] = field(default_factory=dict)
    provider_results: List[ProviderResult] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_url": self.original_url,
            "normalized_url": self.normalized_url,
            "final_url": self.final_url,
            "checked_at": self.checked_at.isoformat() + "Z",
            "verdict": self.verdict,
            "safety_score": self.safety_score,
            "risk_score": self.risk_score,
            "allowed_for_agent": self.allowed_for_agent,
            "findings": [finding.to_dict() for finding in self.findings],
            "redirects": self.redirects,
            "checks": self.checks,
            "provider_results": [result.to_dict() for result in self.provider_results],
            "error": self.error,
        }
