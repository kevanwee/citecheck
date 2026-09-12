"""Resolvers: does this citation correspond to a real authority?

Design:
  - `Resolver.resolve()` returns a Resolution, or None meaning "I don't cover this".
  - `CompositeResolver` asks each in turn; first non-None wins; otherwise UNCHECKED.
  - Offline by default. `ManifestResolver` reads a JSON file of known authorities (a firm's
    library, a matter's bundle index, or test fixtures). HTTP resolvers are opt-in because
    they touch third-party sites whose terms of use you are responsible for honouring.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from .extract import Citation, CitationKind


class Status(StrEnum):
    EXISTS = "exists"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    UNCHECKED = "unchecked"


@dataclass(frozen=True)
class Resolution:
    status: Status
    source: str  # which resolver answered
    url: str | None = None
    title: str | None = None
    note: str = ""


class Resolver(Protocol):
    def resolve(self, citation: Citation) -> Resolution | None: ...


class ManifestResolver:
    """Resolve against a JSON manifest.

    Format:
    {
      "coverage": ["SG:case_neutral", "SG:statute"],      # what this manifest is authoritative for
      "entries": [
        {"key": "[2024] SGHC 123", "title": "...", "url": "..."},
        {"key": "Companies Act 1967 s 157", "url": "..."}
      ]
    }
    A citation whose jurisdiction:kind is in `coverage` but absent from `entries` is
    NOT_FOUND. One outside coverage returns None (not our business).
    """

    def __init__(self, path: Path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.name = f"manifest:{Path(path).name}"
        self.coverage = set(raw.get("coverage", []))
        self.entries = {e["key"]: e for e in raw.get("entries", [])}

    def resolve(self, citation: Citation) -> Resolution | None:
        tag = f"{citation.jurisdiction}:{citation.kind.value}"
        entry = self.entries.get(citation.key)
        if entry is not None:
            return Resolution(Status.EXISTS, self.name, entry.get("url"), entry.get("title"))
        if tag in self.coverage:
            return Resolution(Status.NOT_FOUND, self.name,
                              note="within manifest coverage but absent")
        return None


class HttpExistenceResolver:
    """Opt-in. Checks that a canonical URL for the citation responds 200.

    Existence of a page is strong evidence the citation exists; a 404 is strong evidence it
    does not. It says nothing about what the case holds. Respect the target site's terms of
    use and rate limits; this resolver performs at most one request per unique citation.
    """

    def __init__(self, *, timeout: float = 10.0, user_agent: str = "citecheck/0.1"):
        self.timeout = timeout
        self.user_agent = user_agent
        self.name = "http"

    def resolve(self, citation: Citation) -> Resolution | None:
        if citation.kind is not CitationKind.CASE_NEUTRAL:
            return None
        url = citation.url_hint
        if not url:
            return None
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                final = resp.geturl()
                if resp.status == 200 and _looks_like_judgment(final, citation):
                    return Resolution(Status.EXISTS, self.name, final)
                return Resolution(Status.AMBIGUOUS, self.name, final,
                                  note=f"HTTP {resp.status}; page may not be the judgment")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return Resolution(Status.NOT_FOUND, self.name, url, note="HTTP 404")
            return Resolution(Status.AMBIGUOUS, self.name, url, note=f"HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError) as e:
            return Resolution(Status.AMBIGUOUS, self.name, url, note=f"network: {e}")


def _looks_like_judgment(final_url: str, citation: Citation) -> bool:
    # Some sites redirect unknown ids to a search page instead of 404ing.
    return str(citation.number) in final_url and str(citation.year) in final_url


class CompositeResolver:
    def __init__(self, resolvers: list[Resolver]):
        self.resolvers = resolvers

    def resolve(self, citation: Citation) -> Resolution:
        for r in self.resolvers:
            res = r.resolve(citation)
            if res is not None:
                return res
        return Resolution(Status.UNCHECKED, "none", citation.url_hint,
                          note="no resolver covers this citation")
