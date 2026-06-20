import pytest

from harness import (
    ReferenceMissing,
    assert_stream_match,
    assert_stream_signature,
    reference_path,
)

UTIL = "yes"

# yes: operands ARE the output, streamed forever (space-joined + '\n').
YES_ARG_CASES: list[tuple[str, list[str]]] = [
    ("default", []),
    ("single-word", ["hello"]),
    ("multi-word", ["a", "b", "c"]),
    ("empty-string", [""]),
    ("dash-operand", ["-"]),
    ("double-dash-operand", ["--", "--help"]),
    ("special-chars", ["a\tb", "c d"]),
    ("unicode", ["café", "🚀"]),
    ("newline-operand", ["a\nb"]),
    ("many-words", ["w"] * 100),
    ("unknown-long", ["--bogus"]),
    ("unknown-short", ["-z"]),
    ("help", ["--help"]),
    ("version", ["--version"]),
    ("operand-then-help", ["foo", "--help"]),   # GNU permutes options -> help
    ("help-then-version", ["--help", "--version"]),
    ("version-then-help", ["--version", "--help"]),
]

# banner cases: content is ours by design -> compare signature, not bytes
YES_SIGNATURE_CASE_IDS: frozenset[str] = frozenset({
    "help",
    "version",
    "operand-then-help",
    "help-then-version",
    "version-then-help",
})


@pytest.fixture(scope="module", autouse=True)
def _require_reference():
    try:
        reference_path(UTIL)
    except ReferenceMissing as e:
        pytest.skip(str(e))


@pytest.mark.parametrize(
    "case_id,args", YES_ARG_CASES, ids=[i for i, _ in YES_ARG_CASES]
)
def test_args(case_id, args):
    if case_id in YES_SIGNATURE_CASE_IDS:
        assert_stream_signature(UTIL, args)
    else:
        assert_stream_match(UTIL, args)
