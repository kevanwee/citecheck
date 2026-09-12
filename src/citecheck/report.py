"""Report assembly and exit-code policy."""

from __future__ import annotations

from dataclasses import dataclass, field

from .extract import Citation
from .resolve import Resolution, Status

EXIT_OK = 0
EXIT_NOT_FOUND = 1
EXIT_STRICT_UNRESOLVED = 2


@dataclass
class Row:
    citation: Citation
    resolution: Resolution


@dataclass
class Report:
    rows: list[Row] = field(default_factory=list)
    strict: bool = False

    def counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in Status}
        for r in self.rows:
            out[r.resolution.status.value] += 1
        return out

    @property
    def exit_code(self) -> int:
        c = self.counts()
        if c[Status.NOT_FOUND.value]:
            return EXIT_NOT_FOUND
        if self.strict and (c[Status.UNCHECKED.value] or c[Status.AMBIGUOUS.value]):
            return EXIT_STRICT_UNRESOLVED
        return EXIT_OK

    def to_markdown(self) -> str:
        c = self.counts()
        lines = [
            "# Citation check",
            "",
            f"{len(self.rows)} unique citations: "
            f"{c['exists']} exist, {c['not_found']} NOT FOUND, "
            f"{c['ambiguous']} ambiguous, {c['unchecked']} unchecked."
            + ("  Strict mode: unresolved citations fail the check." if self.strict else ""),
            "",
            "| # | Citation | Kind | Status | Source | Cited for |",
            "|---|---|---|---|---|---|",
        ]
        for i, r in enumerate(self.rows, 1):
            status = r.resolution.status.value.upper()
            if r.resolution.status is Status.NOT_FOUND:
                status = f"**{status}**"
            src = r.resolution.source
            if r.resolution.url:
                src = f"[{src}]({r.resolution.url})"
            ctx = r.citation.context.replace("|", "\\|")
            if len(ctx) > 180:
                ctx = ctx[:177] + "..."
            pin = f" at [{r.citation.pinpoint}]" if r.citation.pinpoint else ""
            occ = f" (x{r.citation.occurrences})" if r.citation.occurrences > 1 else ""
            lines.append(
                f"| {i} | {r.citation.key}{pin}{occ} | {r.citation.kind.value} | {status} | "
                f"{src} | {ctx} |"
            )
        notes = [r for r in self.rows if r.resolution.note]
        if notes:
            lines += ["", "## Notes", ""]
            lines += [f"- {r.citation.key}: {r.resolution.note}" for r in notes]
        lines += [
            "",
            "## Next step",
            "",
            "Existence is necessary, not sufficient. For every EXISTS row, confirm the authority "
            "supports the proposition in *Cited for* (see SKILL.md, step 3).",
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "summary": self.counts(),
            "strict": self.strict,
            "exit_code": self.exit_code,
            "citations": [
                {
                    **r.citation.model_dump(mode="json"),
                    "resolution": {
                        "status": r.resolution.status.value,
                        "source": r.resolution.source,
                        "url": r.resolution.url,
                        "title": r.resolution.title,
                        "note": r.resolution.note,
                    },
                }
                for r in self.rows
            ],
        }


def build_report(citations: list[Citation], resolver, *, strict: bool = False) -> Report:
    return Report(rows=[Row(c, resolver.resolve(c)) for c in citations], strict=strict)
