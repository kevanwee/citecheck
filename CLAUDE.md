# CLAUDE.md — citecheck

Engineering conventions for this repository. They bind AI assistants and humans equally.

## What this is

A citation auditor. The deterministic part (extract, resolve existence, report) is a Python
library. The judgement part (does the authority support the proposition) is a skill
(`SKILL.md`) executed by an assistant with retrieval tools. **Keep the line between the
two absolute.**

## Non-negotiables

1. **Extraction is regex, not a model.** `extract.py` and `patterns.py` never call a model
   and never make a network request. If a citation format is missed, add a pattern with
   tests. Do not "fall back to asking the LLM".
2. **Existence is binary evidence, never inference.** A resolver returns EXISTS only on a
   positive match (manifest entry, or an HTTP 200 whose URL still carries the identifier).
   Anything less is AMBIGUOUS or UNCHECKED. Never map "probably exists" to EXISTS.
3. **Offline by default.** HTTP resolvers are opt-in via `--online`. Never add a default
   network call. Never add scraping of full judgment text to this library; the skill reads
   authorities through whatever tools the session provides.
4. **Exit codes are a contract.** `0` clean, `1` NOT_FOUND present, `2` strict-mode
   unresolved. CI and pre-filing hooks depend on them. Changing them is a major version.
5. **The skill never edits the draft.** It reports. If a user wants edits, the assistant
   confirms first and edits only citations verified with a quotation.

## Layout

```
SKILL.md                 the Claude skill; the repo root IS the skill directory
src/citecheck/
  patterns.py            regexes by jurisdiction; every pattern has +/- tests
  extract.py             Citation model, dedupe, sentence context, url_hint
  resolve.py             Resolver protocol; Manifest (offline), HttpExistence (opt-in), Composite
  report.py              Report, markdown/JSON, exit-code policy
  cli.py                 argparse front-end; .docx reading lives here (optional dep)
examples/                a draft with one fabricated citation + a manifest that catches it
tests/
```

## Testing discipline

- Every regex pattern has at least one positive and one negative test. A pattern PR
  without a negative test is incomplete: the negatives are what keep the report free of
  noise, and noisy reports get ignored.
- `examples/draft.md` must always contain exactly one fabricated citation and the CLI test
  must always catch it. That example is the repo's smoke test and its demo.
- `python -m pytest` and `ruff check src tests` before every commit.

## Style

- Python 3.11+, type hints, `from __future__ import annotations`.
- Pydantic for `Citation`; dataclasses for internal results.
- Line length 100.
- Regexes use named groups and are laid out one clause per line with a comment where the
  clause is non-obvious. A regex nobody can read is a regex nobody can fix.
- Citation keys are normalised to the form a practitioner would type. Test the key string
  literally; do not test via a helper that hides the format.

## Adding a jurisdiction or citation form

1. Pattern in `patterns.py` with named groups `year`, `court`, `number` (+ `volume`,
   `division`, `pinpoint` as applicable). Register it in `CASE_PATTERNS` or
   `STATUTE_PATTERNS`.
2. If a canonical public URL exists, add it to `Citation.url_hint` and document the pattern
   in README under "Online resolution".
3. Tests: positive, negative, and key-format.

## Legal-content conventions

- Verdict vocabulary in `SKILL.md` (SUPPORTS, SUPPORTS_DIFFERENT_PIN, OVERSTATES,
  DOES_NOT_ADDRESS, CONTRADICTS, CANNOT_VERIFY) is fixed. Do not add softer categories.
- `CANNOT_VERIFY` is a legitimate and expected output. Never pressure it toward SUPPORTS.
- README and SKILL.md must state plainly what is *not* checked (currency, short-form
  references, scanned PDFs). Overclaiming here is worse than in most repos.

## Commit hygiene

- Imperative subject, scoped: `patterns(uk): add EWFC and UKUT`.
- One logical change per commit.
- No AI attribution lines or co-author trailers.

## What not to build here

- Judgment retrieval or a case-law corpus. Use the retrieval MCPs that already exist.
- A redliner or draft editor.
- Short-form / "supra" resolution. Out of scope until someone proves the false-positive
  rate is acceptable.
