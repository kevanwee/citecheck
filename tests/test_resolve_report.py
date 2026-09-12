import json
from pathlib import Path

from citecheck import (
    CompositeResolver,
    ManifestResolver,
    Resolution,
    Status,
    build_report,
    extract_citations,
)
from citecheck.cli import main
from citecheck.report import EXIT_NOT_FOUND, EXIT_OK, EXIT_STRICT_UNRESOLVED

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_manifest_resolver_statuses():
    r = ManifestResolver(EXAMPLES / "manifest.json")
    cs = {c.key: c for c in extract_citations(
        "[2013] SGCA 43; [2024] SGHC 987; [2015] UKSC 72; s 2 of the Interpretation Act 1965")}
    assert r.resolve(cs["[2013] SGCA 43"]).status is Status.EXISTS
    assert r.resolve(cs["[2024] SGHC 987"]).status is Status.NOT_FOUND  # in coverage, absent
    assert r.resolve(cs["[2015] UKSC 72"]) is None  # outside coverage
    assert r.resolve(cs["Interpretation Act 1965 s 2"]) is None


def test_composite_falls_through_to_unchecked():
    r = CompositeResolver([ManifestResolver(EXAMPLES / "manifest.json")])
    c = extract_citations("[2015] UKSC 72")[0]
    res = r.resolve(c)
    assert res.status is Status.UNCHECKED
    assert res.url == "https://caselaw.nationalarchives.gov.uk/uksc/2015/72"


class _AllExist:
    def resolve(self, c):
        return Resolution(Status.EXISTS, "stub")


def test_exit_code_policy():
    cs = extract_citations("[2013] SGCA 43 and [2015] UKSC 72")
    manifest = CompositeResolver([ManifestResolver(EXAMPLES / "manifest.json")])
    assert build_report(cs, manifest).exit_code == EXIT_OK  # unchecked is fine non-strict
    assert build_report(cs, manifest, strict=True).exit_code == EXIT_STRICT_UNRESOLVED
    assert build_report(cs, _AllExist(), strict=True).exit_code == EXIT_OK
    bad = extract_citations("[2024] SGHC 987")
    assert build_report(bad, manifest).exit_code == EXIT_NOT_FOUND


def test_markdown_flags_not_found():
    cs = extract_citations("[2024] SGHC 987 at [44]")
    md = build_report(cs, CompositeResolver([ManifestResolver(EXAMPLES / "manifest.json")]))
    text = md.to_markdown()
    assert "**NOT_FOUND**" in text
    assert "[2024] SGHC 987 at [44]" in text


def test_cli_on_example_draft(capsys):
    rc = main([str(EXAMPLES / "draft.md"), "-m", str(EXAMPLES / "manifest.json"), "--json"])
    assert rc == EXIT_NOT_FOUND  # the fabricated [2024] SGHC 987
    out = json.loads(capsys.readouterr().out)
    assert out["summary"]["not_found"] == 1
    assert out["summary"]["exists"] == 2
    keys = [c["key"] for c in out["citations"]]
    assert "[2015] UKSC 72" in keys and "[2016] AC 742" in keys
    assert "Supreme Court of Judicature Act 1969 s 18(2)" in keys


def test_cli_extract_only(capsys):
    assert main([str(EXAMPLES / "draft.md"), "--extract-only"]) == 0
    out = capsys.readouterr().out
    assert "[2013] SGCA 43\tcase_neutral\tSG\tx2" in out
