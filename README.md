# citecheck

Find every authority cited in a draft. Prove each one exists. Then check it says what the
draft says it says.

The first two steps are a deterministic library and CLI. The third is a Claude skill that
uses whatever retrieval tools are in the session. The split is deliberate: regexes do not
hallucinate, and models should not be trusted to extract citations from page 40 of a brief.

```
$ citecheck submissions.docx -m matter-bundle.json --strict

# Citation check

8 unique citations: 2 exist, 1 NOT FOUND, 0 ambiguous, 5 unchecked.  Strict mode: unresolved citations fail the check.

| # | Citation                       | Kind         | Status        | Source   | Cited for                                  |
|---|--------------------------------|--------------|---------------|----------|--------------------------------------------|
| 1 | [2013] SGCA 43 at [101] (x2)   | case_neutral | EXISTS        | manifest | The test for implying a term in fact is ... |
| 3 | [2024] SGHC 987 at [44]        | case_neutral | **NOT_FOUND** | manifest | ... more recently in [2024] SGHC 987 ...    |
...
$ echo $?
1
```

## Why

Lawyers have been sanctioned in several jurisdictions for filing documents containing
citations that do not exist. Every legal MCP server and research tool on offer *retrieves*
law. None of them take a finished draft and audit it. This is the auditor.

## What it does

| Step | Where | How |
|---|---|---|
| 1. Extract | library | Regex patterns for SG (neutral, SLR, statutes), UK (neutral, reports), AU (neutral, reports). Deduplicated, with pinpoints and the sentence each sits in. |
| 2. Resolve | library | Offline by default via a JSON manifest (bundle index, firm library). Opt-in HTTP existence check against canonical URLs. |
| 3. Verify proposition | skill | The assistant reads the authority and classifies: SUPPORTS / OVERSTATES / DOES_NOT_ADDRESS / CONTRADICTS / CANNOT_VERIFY, with quotations. |
| 4. Currency | skill | Reversed / overruled / doubted, to the extent available tools allow; explicit about limits. |
| 5. Report | both | Markdown or JSON; exit code gates CI or a pre-filing hook. |

## Install

```bash
pip install -e ".[dev]"     # library, CLI, tests
pip install -e ".[docx]"    # adds .docx reading (paragraphs, tables, footnotes)
```

As a Claude skill: clone this repo into `.claude/skills/citecheck/` (project) or
`~/.claude/skills/citecheck/` (user). `SKILL.md` at the repo root is the skill.

## CLI

```bash
citecheck draft.md --extract-only                 # list citations, nothing else
citecheck draft.md -m manifest.json               # resolve against a manifest
citecheck draft.md -m a.json -m b.json --online   # several manifests + HTTP check
citecheck draft.md -m manifest.json --strict      # unresolved = failure
citecheck draft.md -m manifest.json --json        # machine-readable
```

Exit codes: `0` clean, `1` at least one citation NOT FOUND, `2` (strict only) at least one
citation unchecked or ambiguous.

## Manifest format

```json
{
  "coverage": ["SG:case_neutral", "SG:statute"],
  "entries": [
    { "key": "[2013] SGCA 43", "title": "Sembcorp Marine v PPL Holdings", "url": "https://..." },
    { "key": "Companies Act 1967 s 157" }
  ]
}
```

`coverage` declares what the manifest is authoritative for. A citation inside coverage but
absent from `entries` is **NOT_FOUND**. One outside coverage is passed to the next resolver
(or reported UNCHECKED). This lets a matter's bundle index act as a hard gate for the
authorities that were supposed to be in the bundle, without making claims about the rest.

## Library

```python
from citecheck import extract_citations, ManifestResolver, CompositeResolver, build_report

cites = extract_citations(open("draft.md").read())
report = build_report(cites, CompositeResolver([ManifestResolver("manifest.json")]), strict=True)
print(report.to_markdown())
raise SystemExit(report.exit_code)
```

Citation keys are normalised the way practitioners write them (`[2013] SGCA 43`,
`(1992) 175 CLR 1`, `Companies Act 1967 s 157`), so manifests can be typed by hand.

## Online resolution

`--online` requests the canonical URL for neutral citations:

- Singapore: `https://www.elitigation.sg/gd/s/<year>_<court>_<number>`
- England & Wales: `https://caselaw.nationalarchives.gov.uk/<court>/<year>/<number>`

A 200 whose final URL still contains the year and number is EXISTS; a 404 is NOT_FOUND;
anything else is AMBIGUOUS with the reason. One request per unique citation, default
10-second timeout. **You are responsible for the terms of use of any site you point this
at.** It is off by default for that reason.

## What it does not do

- It does not decide whether a case is *good law*. Step 4 of the skill covers currency to
  the extent tools allow; there is no free comprehensive Singapore citator.
- It does not extract citations from scanned PDFs. OCR first.
- It does not parse "ibid", "supra" or short-form case names. Those resolve to a full
  citation elsewhere in the draft, which *is* extracted.
- Regexes are conservative. A citation format not in `patterns.py` is silently missed; add
  it with a positive and a negative test.

## Related projects

Pairs with [bundlebuild](https://github.com/kevanwee/bundlebuild) (the bundle index it produces is a valid manifest)
and [chronology](https://github.com/kevanwee/chronology). See also [sg-deadline](https://github.com/kevanwee/sg-deadline).

## License

MIT.
