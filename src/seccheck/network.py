import http.client
import ipaddress
import json
import socket
import ssl
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from .models import Finding, ScanOptions
from .url_utils import hostname_port, split_url


PRIVATE_IP_REASONS = (
    "is_private",
    "is_loopback",
    "is_link_local",
    "is_multicast",
    "is_reserved",
    "is_unspecified",
)


class NetworkError(RuntimeError):
    pass


def resolve_host(host: str, port: int, timeout: float, allow_private: bool = False) -> Tuple[List[str], List[Finding]]:
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    findings = []
    try:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        return [], [
            Finding(
                check="dns",
                severity="high",
                message="DNS resolution failed.",
                evidence={"host": host, "error": str(exc)},
            )
        ]
    finally:
        socket.setdefaulttimeout(old_timeout)

    addresses = sorted({record[4][0] for record in records})
    if not addresses:
        findings.append(Finding(check="dns", severity="high", message="DNS returned no addresses.", evidence={"host": host}))
    for address in addresses:
        ip = ipaddress.ip_address(address)
        reasons = [reason for reason in PRIVATE_IP_REASONS if getattr(ip, reason)]
        if reasons:
            findings.append(
                Finding(
                    check="dns",
                    severity="info" if allow_private else "critical",
                    message="Host resolves to a non-public IP address%s." % (" and private targets are explicitly allowed" if allow_private else ""),
                    weight=0 if allow_private else None,
                    evidence={"host": host, "address": address, "reasons": reasons},
                )
            )
    return addresses, findings


def validate_tls(host: str, port: int, timeout: float) -> Tuple[Dict[str, Any], List[Finding]]:
    findings = []
    data: Dict[str, Any] = {"host": host, "port": port, "valid": False}
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls_sock:
                cert = tls_sock.getpeercert()
                data["valid"] = True
                data["cipher"] = tls_sock.cipher()[0] if tls_sock.cipher() else None
                data["version"] = tls_sock.version()
                data["subject"] = cert.get("subject")
                data["issuer"] = cert.get("issuer")
                not_after = cert.get("notAfter")
                if not_after:
                    expires = datetime.utcfromtimestamp(ssl.cert_time_to_seconds(not_after))
                    data["not_after"] = expires.isoformat() + "Z"
                    days_left = (expires - datetime.utcnow()).days
                    data["days_until_expiry"] = days_left
                    if days_left < 0:
                        findings.append(Finding(check="tls", severity="critical", message="TLS certificate is expired.", evidence=data))
                    elif days_left < 14:
                        findings.append(Finding(check="tls", severity="medium", message="TLS certificate expires soon.", evidence=data))
    except ssl.SSLError as exc:
        data["error"] = str(exc)
        findings.append(Finding(check="tls", severity="critical", message="TLS validation failed.", evidence={"host": host, "error": str(exc)}))
    except OSError as exc:
        data["error"] = str(exc)
        findings.append(Finding(check="tls", severity="high", message="TLS connection failed.", evidence={"host": host, "error": str(exc)}))
    return data, findings


def _request_path(url: str) -> str:
    parsed = split_url(url)
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    return path


def fetch_url(url: str, options: ScanOptions) -> Tuple[Dict[str, Any], List[Finding], List[Dict[str, Any]], Optional[bytes]]:
    current = url
    redirects: List[Dict[str, Any]] = []
    findings: List[Finding] = []
    content: Optional[bytes] = None
    final_response: Dict[str, Any] = {}

    for redirect_index in range(options.max_redirects + 1):
        parsed = split_url(current)
        host, port = hostname_port(parsed)
        addresses, dns_findings = resolve_host(host, port, options.timeout, options.allow_private)
        final_response.setdefault("dns_chain", []).append({"url": current, "host": host, "port": port, "addresses": addresses})
        findings.extend(dns_findings)

        blocked_private = any(finding.severity == "critical" and finding.check == "dns" for finding in dns_findings)
        if blocked_private and not options.allow_private:
            final_response["blocked_before_fetch"] = True
            final_response["blocked_url"] = current
            return final_response, findings, redirects, None

        connection_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        context = ssl.create_default_context() if parsed.scheme == "https" and options.verify_tls else None
        try:
            if parsed.scheme == "https":
                conn = connection_cls(host, port, timeout=options.timeout, context=context)
            else:
                conn = connection_cls(host, port, timeout=options.timeout)
            headers = {
                "User-Agent": options.user_agent,
                "Accept": "text/html,text/plain,application/xhtml+xml,application/json;q=0.8,*/*;q=0.2",
                "Range": "bytes=0-%d" % max(0, options.max_bytes - 1),
                "Connection": "close",
            }
            conn.request("GET", _request_path(current), headers=headers)
            response = conn.getresponse()
            body = response.read(options.max_bytes + 1)
        except Exception as exc:
            findings.append(
                Finding(
                    check="http",
                    severity="high",
                    message="HTTP request failed.",
                    evidence={"url": current, "error": str(exc), "error_type": exc.__class__.__name__},
                )
            )
            return final_response, findings, redirects, None
        finally:
            try:
                conn.close()
            except Exception:
                pass

        headers_dict = {key.lower(): value for key, value in response.getheaders()}
        final_response = {
            "url": current,
            "status": response.status,
            "reason": response.reason,
            "headers": headers_dict,
            "content_type": headers_dict.get("content-type", ""),
            "content_length_header": headers_dict.get("content-length"),
            "sample_bytes": min(len(body), options.max_bytes),
            "truncated": len(body) > options.max_bytes,
            "dns_chain": final_response.get("dns_chain", []),
        }

        if response.status in (301, 302, 303, 307, 308):
            location = headers_dict.get("location")
            if not location:
                findings.append(Finding(check="http", severity="medium", message="Redirect response has no Location header.", evidence=final_response))
                return final_response, findings, redirects, body[: options.max_bytes]
            next_url = urljoin(current, location)
            redirects.append({"from": current, "to": next_url, "status": response.status})
            current = next_url
            continue

        content = body[: options.max_bytes]
        if 400 <= response.status < 500:
            findings.append(Finding(check="http", severity="medium", message="URL returned a client error.", evidence=final_response))
        elif response.status >= 500:
            findings.append(Finding(check="http", severity="medium", message="URL returned a server error.", evidence=final_response))
        return final_response, findings, redirects, content

    findings.append(
        Finding(
            check="http",
            severity="high",
            message="Redirect chain exceeded configured maximum.",
            evidence={"max_redirects": options.max_redirects, "redirects": redirects},
        )
    )
    return final_response, findings, redirects, content


def http_json(url: str, timeout: float, method: str = "GET", body: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    parsed = split_url(url)
    host, port = hostname_port(parsed)
    connection_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    if parsed.scheme == "https":
        conn = connection_cls(host, port, timeout=timeout, context=ssl.create_default_context())
    else:
        conn = connection_cls(host, port, timeout=timeout)
    try:
        conn.request(method, _request_path(url), body=body, headers=headers or {})
        response = conn.getresponse()
        payload = response.read(1024 * 1024)
        decoded = payload.decode("utf-8", errors="replace")
        try:
            data = json.loads(decoded)
        except json.JSONDecodeError:
            data = {"raw": decoded[:2000]}
        data["_http_status"] = response.status
        return data
    finally:
        conn.close()


def parse_http_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return None
