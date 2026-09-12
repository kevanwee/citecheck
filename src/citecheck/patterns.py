"""Citation regexes, grouped by jurisdiction.

Each pattern yields named groups: year, court (or reporter), number, and optionally volume
and pinpoint. Keep patterns conservative: a false negative is a missed check, a false
positive is noise the reviewer learns to ignore, and ignored reports are useless.

When adding a pattern, add a positive AND a negative test in tests/test_extract.py.
"""

from __future__ import annotations

import re

_PIN = r"(?:\s+at\s+\[?(?P<pinpoint>\d+(?:\]\s*[-–]\s*\[\d+)?)\]?)?"

# -- Singapore ---------------------------------------------------------------------------

SG_NEUTRAL = re.compile(
    r"\[(?P<year>\d{4})\]\s+"
    r"(?P<court>SGCA\(I\)|SGCA|SGHC\(A\)|SGHC\(I\)|SGHCF|SGHCR|SGHC|SGDC|SGMC|SGFC|SGYC|"
    r"SGIPOS|SGPDPC|SGSCR|SGSC)\s+"
    r"(?P<number>\d+)" + _PIN
)

SG_SLR = re.compile(
    r"\[(?P<year>\d{4})\]\s+(?P<volume>\d)\s+(?P<court>SLR\(R\)|SLR)\s+(?P<number>\d+)" + _PIN
)

# "s 12(3) of the Companies Act 1967", "section 2 Interpretation Act 1965", "ss 6 and 24A"
SG_STATUTE = re.compile(
    r"\b(?P<prefix>ss?\.?|[Ss]ections?)\s+"
    r"(?P<section>\d+[A-Z]{0,2}(?:\(\d+[A-Za-z]?\))*(?:\([a-z]{1,2}\))?(?:\s*(?:and|to|[-–,])\s*\d+[A-Z]{0,2}(?:\(\d+\))*)*)"
    r"\s+(?:of\s+)?(?:the\s+)?"
    r"(?P<act>(?:[A-Z][A-Za-z'’\-]+(?:\s+(?:[A-Z][A-Za-z'’\-]+|and|of|the|for))*)\s+Act\s+(?P<year>\d{4}))"
)

# -- United Kingdom ----------------------------------------------------------------------

UK_NEUTRAL = re.compile(
    r"\[(?P<year>\d{4})\]\s+"
    r"(?P<court>UKSC|UKHL|UKPC|EWCA\s+Civ|EWCA\s+Crim|EWHC|EWCOP|EWFC|UKUT|UKEAT)\s+"
    r"(?P<number>\d+)"
    r"(?:\s*\((?P<division>Ch|QB|KB|Comm|TCC|Admin|Fam|Pat|IPEC|Admlty|Mercantile)\))?" + _PIN
)

UK_REPORT = re.compile(
    r"\[(?P<year>\d{4})\]\s+(?:(?P<volume>\d)\s+)?"
    r"(?P<court>AC|WLR|All\s+ER|QB|KB|Ch|Lloyd's\s+Rep|BCLC|BCC|FSR|RPC|EMLR)\s+"
    r"(?P<number>\d+)" + _PIN
)

# -- Australia ---------------------------------------------------------------------------

AU_NEUTRAL = re.compile(
    r"\[(?P<year>\d{4})\]\s+"
    r"(?P<court>HCA|FCAFC|FCA|NSWCA|NSWSC|VSCA|VSC|QCA|QSC|WASCA|WASC|SASCA|SASC)\s+"
    r"(?P<number>\d+)" + _PIN
)

AU_REPORT = re.compile(
    r"\((?P<year>\d{4})\)\s+(?P<volume>\d{1,3})\s+(?P<court>CLR|FCR|ALR|NSWLR|VR)\s+"
    r"(?P<number>\d+)" + _PIN
)

CASE_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    # (jurisdiction, kind, pattern) -- order matters where patterns could overlap
    ("SG", "neutral", SG_NEUTRAL),
    ("SG", "report", SG_SLR),
    ("UK", "neutral", UK_NEUTRAL),
    ("UK", "report", UK_REPORT),
    ("AU", "neutral", AU_NEUTRAL),
    ("AU", "report", AU_REPORT),
]

STATUTE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("SG", SG_STATUTE),
]

SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[(])")
