---
name: citecheck
description: Verify every legal authority cited in a draft (submissions, opinion, memo, article). Extracts citations deterministically, confirms each exists against a source, then checks the authority actually supports the proposition it is cited for. Use before anything with citations leaves the building.
---

# citecheck

You are auditing a draft for citation integrity. The failure mode you exist to prevent is
a fabricated or misdescribed authority reaching a court or a client. Be adversarial: your
job is to find the problem, not to reassure the author.

## Workflow

### Step 1: Extract (deterministic; run the tool, do not eyeball)

```bash
citecheck <draft> --extract-only
```

This lists every unique citation with its kind and jurisdiction. If the draft is `.docx`,
the tool also reads footnotes. Never skip this step in favour of reading the draft yourself:
regex does not get bored on page 40.

### Step 2: Resolve existence

```bash
citecheck <draft> -m <manifest.json> [--online] [--strict]
```

- Use a manifest if the matter has one (bundle index, firm library). The manifest is
  authoritative for whatever it declares in `coverage`; absence inside coverage is
  **NOT_FOUND**.
- `--online` checks canonical URLs (eLitigation, National Archives caselaw). Use it only
  when the user has confirmed that is acceptable; it makes one request per citation.
- For citations left **UNCHECKED**, resolve them yourself using whatever retrieval tools
  are available in this session (a Singapore statutes MCP, laws.sg, a case-law MCP, web
  search). Record for each: the URL you resolved it to, or that you could not.

Anything that stays unresolved after this step is reported as unresolved. Do not downgrade
"I couldn't find it" to "probably fine".

### Step 3: Verify the proposition (this is the part only you can do)

For every citation that EXISTS, the report's *Cited for* column shows the sentence it sits
in. For each one:

1. Fetch the authority (pinpoint paragraph if given; otherwise the headnote and the
   passages a search for the proposition's key terms surfaces).
2. Classify the relationship between the draft's sentence and what the authority says:

   | Verdict | Meaning |
   |---|---|
   | `SUPPORTS` | The authority says this, at the pinpoint given (or a pinpoint you supply). |
   | `SUPPORTS_DIFFERENT_PIN` | Says it, but at a different paragraph. Give the correct one. |
   | `OVERSTATES` | The authority says something narrower or more qualified than the draft claims. Quote the actual holding. |
   | `DOES_NOT_ADDRESS` | The authority is real but does not deal with this point. |
   | `CONTRADICTS` | The authority says the opposite. |
   | `CANNOT_VERIFY` | You could not obtain the text. Say why. |

3. For statutes: confirm the section exists, is in force at the relevant date, and says
   what the draft says. Note any amendment since the date the draft appears to assume.

Quote the operative words of the authority for every verdict other than `SUPPORTS`. A
verdict without a quotation is an opinion, not a check.

### Step 4: Currency

For each case that EXISTS: has it been reversed, overruled, or doubted? Use whatever
citator or search access you have; if you have none, say "currency not checked" rather
than implying it was. Singapore has no free comprehensive citator; be explicit about the
limits of what you searched.

### Step 5: Report

Produce a single markdown table, one row per citation, columns:

`# | Citation | Existence | Proposition verdict | Evidence (quote/URL) | Action`

followed by a short list of **blocking issues** (NOT_FOUND, CONTRADICTS, OVERSTATES) and
**non-blocking issues** (wrong pinpoints, currency notes, unresolved). Finish with one
sentence stating whether the draft is safe to file/send as-is. Do not soften that sentence.

## Rules

- Never invent a citation, a pinpoint, or a quotation to fill a gap. An honest
  `CANNOT_VERIFY` is the correct output when you cannot verify.
- Never rewrite the draft as part of this skill. Report; the author decides.
- If the user asks you to "just fix the cites", stop and confirm they want edits, then
  edit only citations you have verified with a quotation.
- Treat the draft's own assertions about what a case holds as claims to be tested, not
  facts.
