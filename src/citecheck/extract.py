"""Citation extraction. Pure regex; deterministic; no network; no model."""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field

from .patterns import CASE_PATTERNS, SENTENCE_BOUNDARY, STATUTE_PATTERNS


class CitationKind(StrEnum):
    CASE_NEUTRAL = "case_neutral"
    CASE_REPORT = "case_report"
    STATUTE = "statute"


class Mention(BaseModel):
    raw: str
    start: int
    end: int
    pinpoint: str | None = None
    context: str


class Citation(BaseModel):
    kind: CitationKind
    jurisdiction: str
    raw: str
    key: str  # normalised identity used for dedupe and manifest lookup
    year: int | None = None
    court: str | None = None  # court abbreviation or report series or Act name
    number: str | None = None
    volume: str | None = None
    division: str | None = None
    pinpoint: str | None = None
    start: int
    end: int
    context: str  # the sentence the citation sits in; the proposition it is cited for
    occurrences: int = 1
    mentions: list[Mention] = Field(default_factory=list)

    @property
    def url_hint(self) -> str | None:
        """Best-effort canonical source URL, for the reviewer. Not used for resolution."""
        if self.kind is CitationKind.CASE_NEUTRAL and self.jurisdiction == "SG":
            return f"https://www.elitigation.sg/gd/s/{self.year}_{self.court}_{self.number}"
        if self.kind is CitationKind.CASE_NEUTRAL and self.jurisdiction == "UK":
            court = (self.court or "").lower().replace(" ", "/")
            div = f"/{self.division.lower()}" if self.division else ""
            return f"https://caselaw.nationalarchives.gov.uk/{court}{div}/{self.year}/{self.number}"
        if self.kind is CitationKind.STATUTE and self.jurisdiction == "SG":
            # SSO slugs are the initials of the capitalised words incl. "Act": "Companies
            # Act 1967" -> CA1967, "Supreme Court of Judicature Act 1969" -> SCJA1969.
            initials = "".join(w[0] for w in (self.court or "").split() if w[0].isupper())
            return f"https://sso.agc.gov.sg/Act/{initials}{self.year}"
        return None


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _sentence_around(text: str, start: int, end: int) -> str:
    left, right = 0, len(text)
    for boundary in SENTENCE_BOUNDARY.finditer(text):
        if boundary.end() <= start:
            left = boundary.end()
        elif boundary.start() >= end:
            right = boundary.start()
            break
    return _norm_ws(text[left:right])


def _case_key(raw: str, court: str, year: str, number: str, volume: str | None) -> str:
    # Round-bracket years (e.g. "(1992) 175 CLR 1") mean the year is descriptive, not part of
    # the identifier; preserve the style so keys match how practitioners write them.
    open_, close = ("(", ")") if raw.lstrip().startswith("(") else ("[", "]")
    court = _norm_ws(court)
    if volume:
        return f"{open_}{year}{close} {volume} {court} {number}"
    return f"{open_}{year}{close} {court} {number}"


def extract_citations(text: str) -> list[Citation]:
    """Return deduplicated citations in order of first appearance."""
    found: dict[str, Citation] = {}
    order: list[str] = []

    def add(c: Citation) -> None:
        mention = Mention(**c.model_dump(include={"raw", "start", "end", "pinpoint", "context"}))
        if c.key in found:
            found[c.key].occurrences += 1
            found[c.key].mentions.append(mention)
            return
        c.mentions = [mention]
        found[c.key] = c
        order.append(c.key)

    for jurisdiction, kind, pattern in CASE_PATTERNS:
        for m in pattern.finditer(text):
            gd = m.groupdict()
            key = _case_key(m.group(0), gd["court"], gd["year"], gd["number"], gd.get("volume"))
            add(Citation(
                kind=CitationKind.CASE_NEUTRAL if kind == "neutral" else CitationKind.CASE_REPORT,
                jurisdiction=jurisdiction,
                raw=_norm_ws(m.group(0)),
                key=key,
                year=int(gd["year"]),
                court=_norm_ws(gd["court"]),
                number=gd["number"],
                volume=gd.get("volume"),
                division=gd.get("division"),
                pinpoint=gd.get("pinpoint"),
                start=m.start(),
                end=m.end(),
                context=_sentence_around(text, m.start(), m.end()),
            ))

    for jurisdiction, pattern in STATUTE_PATTERNS:
        for m in pattern.finditer(text):
            gd = m.groupdict()
            act = _norm_ws(gd["act"])
            section = _norm_ws(gd["section"])
            add(Citation(
                kind=CitationKind.STATUTE,
                jurisdiction=jurisdiction,
                raw=_norm_ws(m.group(0)),
                key=f"{act} s {section}",
                year=int(gd["year"]),
                court=act,
                number=section,
                start=m.start(),
                end=m.end(),
                context=_sentence_around(text, m.start(), m.end()),
            ))

    return sorted((found[k] for k in order), key=lambda c: c.start)
