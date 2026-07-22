import os
from typing import Iterable, List


def _candidate_roots() -> List[str]:
    roots = [os.getcwd()]
    here = os.path.abspath(os.path.dirname(__file__))
    # src/sancheck -> repo root (../../) and plugin scripts/src/sancheck -> plugin root (../../..)
    roots.append(os.path.abspath(os.path.join(here, "..", "..")))
    roots.append(os.path.abspath(os.path.join(here, "..", "..", "..")))
    return roots


def _walk_up(start: str, limit: int = 6) -> Iterable[str]:
    cur = os.path.abspath(start)
    for _ in range(limit):
        yield cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent


def _parse_env_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not key:
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            # Project .env wins over a broken/stale shell export.
            os.environ[key] = value


def load_env_file() -> None:
    seen = set()
    for root in _candidate_roots():
        for directory in _walk_up(root):
            path = os.path.join(directory, ".env")
            if path in seen:
                continue
            seen.add(path)
            if os.path.isfile(path):
                _parse_env_file(path)
                return
