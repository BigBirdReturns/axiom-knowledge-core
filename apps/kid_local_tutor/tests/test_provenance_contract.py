import types

from kid_local_tutor.provenance import validate_provenance_contract, enforce_provenance_contract


def _res(doc: str):
    return types.SimpleNamespace(document=doc, metadata={}, distance=0.0)


def test_rejects_uncited_claims():
    results = [_res("Some context\nCITATIONS:\nsources/seed/first_aid_basics.md span=1-10")]
    text = "Wash the wound with clean water."
    ok, report = validate_provenance_contract(text, results)
    assert ok is False
    assert "Missing citation" in report


def test_rejects_invalid_citation_number():
    results = [_res("Context\nCITATIONS:\nsources/seed/first_aid_basics.md span=1-10")]
    text = "Wash the wound with clean water. [2]"
    ok, report = validate_provenance_contract(text, results)
    assert ok is False
    assert "Invalid citation" in report


def test_allows_explicit_unknown_without_citations():
    results = [_res("Context\nCITATIONS:\nsources/seed/first_aid_basics.md span=1-10")]
    text = "I do not know from this local library."
    ok, report = validate_provenance_contract(text, results)
    assert ok is True
    assert report == ""


def test_appends_sources_block_when_missing():
    results = [
        _res("Context A\nCITATIONS:\nsources/a.md span=1-2"),
        _res("Context B\nCITATIONS:\nsources/b.md span=3-4"),
    ]
    text = "Claim one. [1] Claim two. [2]"
    out = enforce_provenance_contract(text, results)
    assert "Sources:" in out
    assert "[1]" in out
    assert "[2]" in out
