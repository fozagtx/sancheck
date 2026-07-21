import re
from dataclasses import dataclass, field
from typing import Dict, List

from .models import Finding
from .url_utils import safe_excerpt


@dataclass
class PromptMatch:
    label: str
    severity: str
    weight: int
    excerpt: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "severity": self.severity,
            "weight": self.weight,
            "excerpt": self.excerpt,
        }


@dataclass
class PromptInjectionReport:
    score: int
    severity: str
    matches: List[PromptMatch] = field(default_factory=list)
    hidden_instruction_matches: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "score": self.score,
            "severity": self.severity,
            "hidden_instruction_matches": self.hidden_instruction_matches,
            "matches": [match.to_dict() for match in self.matches],
        }


PATTERNS = [
    (
        "instruction_override",
        "critical",
        35,
        re.compile(r"\b(ignore|disregard|forget|override)\b.{0,80}\b(previous|prior|above|system|developer|all)\b.{0,40}\binstructions?\b", re.I | re.S),
    ),
    (
        "role_reassignment",
        "high",
        20,
        re.compile(r"\byou are (now|no longer|actually)\b.{0,80}\b(system|developer|assistant|admin|root)\b", re.I | re.S),
    ),
    (
        "secret_exfiltration",
        "critical",
        40,
        re.compile(r"\b(reveal|print|dump|exfiltrate|send|upload)\b.{0,80}\b(system prompt|developer message|api key|token|secret|credentials?)\b", re.I | re.S),
    ),
    (
        "tool_abuse",
        "high",
        25,
        re.compile(r"\b(run|execute|call|invoke)\b.{0,80}\b(shell|terminal|tool|function|browser|python|curl|wget)\b", re.I | re.S),
    ),
    (
        "data_smuggling",
        "high",
        20,
        re.compile(r"\b(base64|rot13|hex encode|url encode|steganograph|hidden message)\b", re.I),
    ),
    (
        "jailbreak_marker",
        "medium",
        15,
        re.compile(r"\b(jailbreak|DAN mode|developer mode|unfiltered mode|prompt injection)\b", re.I),
    ),
    (
        "prompt_boundary",
        "medium",
        10,
        re.compile(r"(?:<\|system\|>|<\|developer\|>|###\s*(system|developer|instruction)|BEGIN\s+(SYSTEM|DEVELOPER|PROMPT|INSTRUCTIONS))", re.I),
    ),
]

HIDDEN_CHUNK_PATTERNS = [
    re.compile(r"<!--(?P<body>.*?)-->", re.I | re.S),
    re.compile(r"<[^>]+(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|font-size\s*:\s*0)[^>]*>(?P<body>.*?)</[^>]+>", re.I | re.S),
    re.compile(r"<[^>]+aria-hidden=[\"']?true[\"']?[^>]*>(?P<body>.*?)</[^>]+>", re.I | re.S),
]


def strip_markup(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def analyze_prompt_injection(content: bytes, content_type: str) -> PromptInjectionReport:
    decoded = content.decode("utf-8", errors="replace")
    searchable = decoded
    if "html" in content_type.lower():
        searchable = decoded + "\n" + strip_markup(decoded)

    matches = []
    seen = set()
    for label, severity, weight, pattern in PATTERNS:
        for match in pattern.finditer(searchable):
            key = (label, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                PromptMatch(
                    label=label,
                    severity=severity,
                    weight=weight,
                    excerpt=safe_excerpt(searchable, match.start(), match.end()),
                )
            )
            if len(matches) >= 20:
                break

    hidden_instruction_matches = 0
    if "html" in content_type.lower():
        for hidden_pattern in HIDDEN_CHUNK_PATTERNS:
            for hidden in hidden_pattern.finditer(decoded):
                body = hidden.group("body")
                nested = analyze_prompt_injection(body.encode("utf-8", errors="ignore"), "text/plain")
                hidden_instruction_matches += len(nested.matches)
                for nested_match in nested.matches:
                    matches.append(
                        PromptMatch(
                            label="hidden_" + nested_match.label,
                            severity=nested_match.severity,
                            weight=nested_match.weight + 10,
                            excerpt=nested_match.excerpt,
                        )
                    )

    score = min(100, sum(match.weight for match in matches))
    if any(match.severity == "critical" for match in matches) or score >= 50:
        severity = "critical"
    elif score >= 25:
        severity = "high"
    elif score >= 10:
        severity = "medium"
    elif score > 0:
        severity = "low"
    else:
        severity = "info"
    return PromptInjectionReport(score=score, severity=severity, matches=matches, hidden_instruction_matches=hidden_instruction_matches)


def finding_from_prompt_report(report: PromptInjectionReport) -> Finding:
    if report.score <= 0:
        return Finding(
            check="prompt_injection",
            severity="info",
            message="No prompt-injection patterns found in fetched content sample.",
            weight=0,
            evidence=report.to_dict(),
        )
    return Finding(
        check="prompt_injection",
        severity=report.severity,
        message="Fetched content contains instructions that appear hostile to AI agents.",
        weight=max(15, report.score),
        evidence=report.to_dict(),
    )

