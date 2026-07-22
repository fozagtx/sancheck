import argparse
import json
import sys
from typing import Any, Dict, Iterable, List

from .models import ScanOptions, ScanReport
from .scanner import scan_url
from .url_utils import extract_urls


VERDICT_ORDER = {"safe": 0, "caution": 1, "unsafe": 2}


def _options_from_args(args: argparse.Namespace) -> ScanOptions:
    return ScanOptions(
        timeout=args.timeout,
        max_redirects=args.max_redirects,
        max_bytes=args.max_bytes,
        allow_private=args.allow_private,
        verify_tls=not args.no_verify_tls,
        enable_threat_intel=not args.no_threat_intel,
        check_domain_age=not args.no_domain_age,
    )


def _print_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _format_text_report(report: ScanReport) -> str:
    lines = [
        "URL: %s" % report.original_url,
        "Final: %s" % (report.final_url or "n/a"),
        "Verdict: %s  Safety: %s/10  Risk: %s/100  Agent allowed: %s"
        % (report.verdict.upper(), report.safety_score, report.risk_score, "yes" if report.allowed_for_agent else "no"),
    ]
    if report.findings:
        lines.append("Findings:")
        for finding in sorted(report.findings, key=lambda item: item.risk_weight(), reverse=True):
            if finding.severity == "info":
                continue
            lines.append("  - [%s] %s: %s" % (finding.severity, finding.check, finding.message))
    else:
        lines.append("Findings: none")
    skipped = [result for result in report.provider_results if result.status == "skipped"]
    if skipped:
        lines.append("Skipped providers: %s" % ", ".join(result.provider for result in skipped))
    return "\n".join(lines)


def _scan_many(urls: Iterable[str], options: ScanOptions) -> List[ScanReport]:
    reports = []
    for url in urls:
        reports.append(scan_url(url, options))
    return reports


def _dedupe_urls(urls: Iterable[str]) -> List[str]:
    deduped = []
    seen = set()
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def _reports_payload(reports: List[ScanReport], allow_verdict: str, mode: str) -> Dict[str, Any]:
    blocked = [report for report in reports if not _allowed_by_policy(report, allow_verdict)]
    return {
        "tool": "sancheck",
        "mode": mode,
        "allowed": len(blocked) == 0,
        "decision": "allow" if len(blocked) == 0 else "block",
        "policy": {"allow_verdict": allow_verdict, "agent_strict": allow_verdict == "safe"},
        "url_count": len(reports),
        "blocked_urls": [report.original_url for report in blocked],
        "reports": [report.to_dict() for report in reports],
    }


def _urls_from_json_payload(payload: Any) -> List[str]:
    urls: List[str] = []
    if isinstance(payload, str):
        urls.extend(extract_urls(payload))
    elif isinstance(payload, list):
        for item in payload:
            urls.extend(_urls_from_json_payload(item))
    elif isinstance(payload, dict):
        for key in ("url", "href"):
            value = payload.get(key)
            if isinstance(value, str):
                urls.append(value)
        for key in ("urls", "links"):
            value = payload.get(key)
            if isinstance(value, list):
                urls.extend(str(item) for item in value if isinstance(item, str))
        for key in ("text", "content", "prompt", "input", "body"):
            value = payload.get(key)
            if isinstance(value, str):
                urls.extend(extract_urls(value))
        messages = payload.get("messages")
        if isinstance(messages, list):
            for message in messages:
                urls.extend(_urls_from_json_payload(message))
    return urls


def command_scan(args: argparse.Namespace) -> int:
    options = _options_from_args(args)
    reports = _scan_many(args.urls, options)
    if args.format == "json":
        _print_json({"reports": [report.to_dict() for report in reports]})
    else:
        print("\n\n".join(_format_text_report(report) for report in reports))
    return 0 if all(report.allowed_for_agent for report in reports) else 2


def _allowed_by_policy(report: ScanReport, allow_verdict: str) -> bool:
    return VERDICT_ORDER[report.verdict] <= VERDICT_ORDER[allow_verdict]


def command_gate(args: argparse.Namespace) -> int:
    text = ""
    urls = list(args.urls or [])
    if args.stdin:
        text = sys.stdin.read()
        urls.extend(extract_urls(text))
    deduped = _dedupe_urls(urls)

    options = _options_from_args(args)
    reports = _scan_many(deduped, options)
    payload = _reports_payload(reports, args.allow_verdict, "gate")
    if args.format == "json":
        _print_json(payload)
    else:
        if not deduped:
            print("No URLs found.")
        elif payload["allowed"]:
            print("Allowed: all %d URL(s) passed." % len(deduped))
        else:
            blocked = [report for report in reports if not _allowed_by_policy(report, args.allow_verdict)]
            print("Blocked: %d of %d URL(s) failed policy." % (len(blocked), len(deduped)))
            for report in blocked:
                print("- %s -> %s (%s risk)" % (report.original_url, report.verdict, report.risk_score))
    return 0 if payload["allowed"] else 2


def command_middleware(args: argparse.Namespace) -> int:
    stdin_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    urls = list(args.urls or [])
    if stdin_text:
        try:
            payload = json.loads(stdin_text)
        except json.JSONDecodeError:
            urls.extend(extract_urls(stdin_text))
        else:
            urls.extend(_urls_from_json_payload(payload))

    deduped = _dedupe_urls(urls)
    options = _options_from_args(args)
    reports = _scan_many(deduped, options)
    payload = _reports_payload(reports, args.allow_verdict, "middleware")
    payload["middleware"] = {
        "contract": "stdin text or JSON in, JSON decision out, exit 2 on block",
        "safe_to_continue": payload["allowed"],
    }
    _print_json(payload)
    return 0 if payload["allowed"] else 2


def command_extract(args: argparse.Namespace) -> int:
    if args.file == "-":
        text = sys.stdin.read()
    else:
        with open(args.file, "r", encoding="utf-8") as handle:
            text = handle.read()
    for url in extract_urls(text):
        print(url)
    return 0


def add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--timeout", type=float, default=5.0, help="network timeout in seconds")
    parser.add_argument("--max-redirects", type=int, default=5, help="maximum redirects to follow")
    parser.add_argument("--max-bytes", type=int, default=65536, help="maximum response bytes to inspect")
    parser.add_argument("--allow-private", action="store_true", help="allow fetching private, loopback, or reserved IP targets")
    parser.add_argument("--no-verify-tls", action="store_true", help="disable TLS certificate verification")
    parser.add_argument("--no-threat-intel", action="store_true", help="skip external threat-intel providers")
    parser.add_argument("--no-domain-age", action="store_true", help="skip RDAP domain age lookup")
    parser.add_argument("--format", choices=("json", "text"), default="text", help="output format")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sancheck", description="Real URL scanner and link-safety gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="scan one or more URLs")
    scan_parser.add_argument("urls", nargs="+")
    add_common_options(scan_parser)
    scan_parser.set_defaults(func=command_scan)

    gate_parser = subparsers.add_parser("gate", help="gate URLs from args or stdin for agent-safe use")
    gate_parser.add_argument("urls", nargs="*")
    gate_parser.add_argument("--stdin", action="store_true", help="read text from stdin and extract URLs")
    gate_parser.add_argument("--allow-verdict", choices=("safe", "caution", "unsafe"), default="safe", help="maximum verdict allowed by policy")
    add_common_options(gate_parser)
    gate_parser.set_defaults(func=command_gate)

    middleware_parser = subparsers.add_parser("middleware", help="agent middleware: read stdin or URLs and emit a JSON allow/block decision")
    middleware_parser.add_argument("urls", nargs="*")
    middleware_parser.add_argument("--allow-verdict", choices=("safe", "caution", "unsafe"), default="safe", help="maximum verdict allowed by policy")
    add_common_options(middleware_parser)
    middleware_parser.set_defaults(func=command_middleware)

    extract_parser = subparsers.add_parser("extract", help="extract URLs from a file or stdin")
    extract_parser.add_argument("file", help="file to scan, or '-' for stdin")
    extract_parser.set_defaults(func=command_extract)
    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print("sancheck: %s: %s" % (exc.__class__.__name__, exc), file=sys.stderr)
        return 1
