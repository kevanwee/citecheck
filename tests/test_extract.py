from citecheck import CitationKind, extract_citations


def keys(text):
    return [c.key for c in extract_citations(text)]


def test_sg_neutral_with_pinpoint():
    cs = extract_citations("See Sembcorp [2013] SGCA 43 at [101].")
    assert len(cs) == 1
    c = cs[0]
    assert c.key == "[2013] SGCA 43"
    assert c.kind is CitationKind.CASE_NEUTRAL
    assert c.jurisdiction == "SG"
    assert c.pinpoint == "101"
    assert c.url_hint == "https://www.elitigation.sg/gd/s/2013_SGCA_43"


def test_sg_court_variants():
    assert keys("[2024] SGHC(A) 5; [2023] SGHC(I) 2; [2022] SGHCR 9; [2021] SGDC 100") == [
        "[2024] SGHC(A) 5", "[2023] SGHC(I) 2", "[2022] SGHCR 9", "[2021] SGDC 100"]


def test_slr_report():
    cs = extract_citations("[2013] 4 SLR 193 and [2009] 3 SLR(R) 883")
    assert [c.key for c in cs] == ["[2013] 4 SLR 193", "[2009] 3 SLR(R) 883"]
    assert cs[0].kind is CitationKind.CASE_REPORT
    assert cs[0].volume == "4"


def test_uk_neutral_and_report():
    cs = extract_citations(
        "[2015] UKSC 72, [2016] AC 742; [2020] EWHC 123 (Comm); [2019] EWCA Civ 7")
    assert [c.key for c in cs] == ["[2015] UKSC 72", "[2016] AC 742", "[2020] EWHC 123",
                                   "[2019] EWCA Civ 7"]
    assert cs[2].division == "Comm"
    assert cs[2].url_hint == "https://caselaw.nationalarchives.gov.uk/ewhc/comm/2020/123"


def test_au_neutral_and_report():
    assert keys("[2012] HCA 4 and (1992) 175 CLR 1") == ["[2012] HCA 4", "(1992) 175 CLR 1"]


def test_statute_forms():
    text = ("under s 18(2) of the Supreme Court of Judicature Act 1969, section 2 of the "
            "Interpretation Act 1965, and ss 6(1) and 24A of the Limitation Act 1959")
    cs = [c for c in extract_citations(text) if c.kind is CitationKind.STATUTE]
    assert [c.key for c in cs] == [
        "Supreme Court of Judicature Act 1969 s 18(2)",
        "Interpretation Act 1965 s 2",
        "Limitation Act 1959 s 6(1) and 24A",
    ]


def test_dedupe_counts_occurrences_and_keeps_first_position():
    cs = extract_citations("A [2013] SGCA 43 at [101]. B. C [2013] SGCA 43 again.")
    assert len(cs) == 1
    assert cs[0].occurrences == 2
    assert cs[0].pinpoint == "101"


def test_context_is_the_containing_sentence():
    text = "First sentence. The test is in [2013] SGCA 43 at [101]. Third sentence."
    c = extract_citations(text)[0]
    assert c.context == "The test is in [2013] SGCA 43 at [101]."


def test_negatives():
    assert keys("Section 12 of the report. In 2013 the SGCA decided 43 cases. [2013] 43") == []
    assert keys("The figure was [2019] million.") == []


def test_order_is_by_position_across_kinds():
    text = "s 2 of the Interpretation Act 1965 then [2013] SGCA 43 then [2015] UKSC 72"
    assert keys(text) == ["Interpretation Act 1965 s 2", "[2013] SGCA 43", "[2015] UKSC 72"]
