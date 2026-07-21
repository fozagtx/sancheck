import posixpath
import re
from typing import Iterable, List, Optional, Tuple
from urllib.parse import SplitResult, quote, unquote, urlsplit, urlunsplit

URL_RE = re.compile(
    r"(?P<url>https?://[^\s<>'\"`)\]]+|www\.[^\s<>'\"`)\]]+)",
    re.IGNORECASE,
)

TRAILING_PUNCTUATION = ".,;:!?"


class UrlError(ValueError):
    pass


def extract_urls(text: str) -> List[str]:
    seen = set()
    urls = []
    for match in URL_RE.finditer(text):
        url = match.group("url").rstrip(TRAILING_PUNCTUATION)
        if url.lower().startswith("www."):
            url = "https://" + url
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def normalize_url(raw_url: str) -> str:
    raw_url = raw_url.strip()
    if not raw_url:
        raise UrlError("URL is empty")
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    if "://" not in raw_url:
        raw_url = "https://" + raw_url

    parsed = urlsplit(raw_url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise UrlError("Only http and https URLs are supported")
    if not parsed.hostname:
        raise UrlError("URL must include a hostname")

    host = parsed.hostname.rstrip(".")
    try:
        ascii_host = host.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise UrlError("Hostname cannot be IDNA-encoded") from exc

    netloc = ascii_host
    if parsed.port:
        default_port = 443 if parsed.scheme.lower() == "https" else 80
        if parsed.port != default_port:
            netloc = "%s:%s" % (netloc, parsed.port)

    path = parsed.path or "/"
    path = quote(unquote(path), safe="/:@-._~!$&'()*+,;=")
    path = posixpath.normpath(path)
    if not path.startswith("/"):
        path = "/" + path
    if parsed.path.endswith("/") and not path.endswith("/"):
        path += "/"

    query = quote(unquote(parsed.query), safe="=&?/:@-._~!$'()*+,;%")
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def split_url(url: str) -> SplitResult:
    parsed = urlsplit(url)
    if not parsed.hostname:
        raise UrlError("URL must include a hostname")
    return parsed


def hostname_port(parsed: SplitResult) -> Tuple[str, int]:
    if not parsed.hostname:
        raise UrlError("URL must include a hostname")
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return parsed.hostname, port


def parent_domains(host: str) -> Iterable[str]:
    labels = host.rstrip(".").split(".")
    for index in range(0, max(0, len(labels) - 1)):
        candidate = ".".join(labels[index:])
        if "." in candidate:
            yield candidate


def has_userinfo(raw_url: str) -> bool:
    parsed = urlsplit(raw_url if "://" in raw_url else "https://" + raw_url)
    return "@" in parsed.netloc.split("@")[0:] and parsed.username is not None


def safe_excerpt(text: str, start: int, end: int, radius: int = 80) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    excerpt = re.sub(r"\s+", " ", text[left:right]).strip()
    if left > 0:
        excerpt = "..." + excerpt
    if right < len(text):
        excerpt += "..."
    return excerpt[:240]

