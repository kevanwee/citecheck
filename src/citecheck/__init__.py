"""citecheck: find every authority cited in a draft and verify that it exists.

Deterministic core:
    extract_citations(text)      -> list[Citation]   regex-based, no model
    Resolver implementations     -> Resolution       manifest (offline) or HTTP (opt-in)
    build_report(...)            -> Report           markdown/JSON + exit code

The *proposition* check (does the authority actually say what the draft says it says) needs
the source text and a reader. That step is specified in SKILL.md and is performed by the
assistant, never by this library.
"""

from .extract import Citation, CitationKind, extract_citations
from .report import Report, build_report
from .resolve import (
    CompositeResolver,
    ManifestResolver,
    Resolution,
    Resolver,
    Status,
)

__all__ = [
    "Citation",
    "CitationKind",
    "extract_citations",
    "Resolver",
    "Resolution",
    "Status",
    "ManifestResolver",
    "CompositeResolver",
    "Report",
    "build_report",
]

__version__ = "0.1.0"
