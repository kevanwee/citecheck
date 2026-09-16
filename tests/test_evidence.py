import io

from citecheck import extract_citations
from citecheck.resolve import HttpExistenceResolver, Status


def test_every_pinpoint_and_context_survives_deduplication():
    text = "First.   Alpha [2013] SGCA 43 at [101].\n\nBeta [2013] SGCA 43 at [105]."
    citation = extract_citations(text)[0]
    assert [m.pinpoint for m in citation.mentions] == ["101", "105"]
    assert citation.mentions[1].context == "Beta [2013] SGCA 43 at [105]."
    assert all(text[m.start:m.end] == m.raw for m in citation.mentions)


class Response(io.BytesIO):
    status = 200

    def geturl(self):
        return "https://www.elitigation.sg/gd/s/2013_SGCA_43"


def test_http_success_requires_identity_metadata(monkeypatch):
    citation = extract_citations("[2013] SGCA 43")[0]
    for body, expected in [
        (b"<title>Sign in</title><p>[2013] SGCA 43</p>", Status.AMBIGUOUS),
        (b"<title>[2013] SGCA 430</title>", Status.AMBIGUOUS),
        (b"<title>[2013] SGCA 43</title>", Status.EXISTS),
    ]:
        monkeypatch.setattr("urllib.request.urlopen", lambda *a, body=body, **k: Response(body))
        assert HttpExistenceResolver().resolve(citation).status is expected


def test_wrong_host_is_not_a_source_match():
    from citecheck.resolve import _looks_like_judgment

    c = extract_citations("[2013] SGCA 43")[0]
    assert not _looks_like_judgment("https://example.com/2013/43", c)
    assert not _looks_like_judgment("https://www.elitigation.sg/search?year=2013&id=43", c)
