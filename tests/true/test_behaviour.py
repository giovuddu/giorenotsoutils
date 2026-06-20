import pytest

from harness import (
    ReferenceMissing,
    assert_match,
    assert_signature_match,
    reference_path,
)

UTIL = "true"

# true/false: operands are ignored; same arg handling for both.
ARG_CASES: list[tuple[str, list[str]]] = [
    ("no-args", []),
    ("single-operand", ["foo"]),
    ("multi-operand", ["foo", "bar", "baz"]),
    ("empty-operand", [""]),
    ("dash-operand", ["-"]),
    ("double-dash", ["--"]),
    ("double-dash-then-flag", ["--", "--help"]),
    ("help", ["--help"]),
    ("version", ["--version"]),
    ("help-then-version", ["--help", "--version"]),
    ("version-then-help", ["--version", "--help"]),
    ("operand-then-help", ["foo", "--help"]),
    ("help-abbrev", ["--hel"]),
    ("help-shortest-abbrev", ["--h"]),
    ("version-abbrev", ["--vers"]),
    ("help-with-arg", ["--help=foo"]),
    ("unknown-long", ["--nonexistent"]),
    ("unknown-short", ["-z"]),
    ("bundled-short", ["-abc"]),
    ("newline-operand", ["\n"]),
    ("special-chars", ["a b\tc", "x\ny"]),
    ("unicode", ["café", "日本語", "🚀"]),
    ("many-operands", ["x"] * 1000),
]

# banner cases: content is ours by design -> compare signature, not bytes
SIGNATURE_CASE_IDS: frozenset[str] = frozenset({
    "help",
    "version",
    "help-then-version",
    "version-then-help",
})

STDIN_CASES: list[tuple[str, bytes]] = [
    ("empty-stdin", b""),
    ("text-stdin", b"hello\nworld\n"),
    ("binary-stdin", bytes(range(256))),
    ("large-stdin", b"A" * (1 << 20)),
    ("no-trailing-newline", b"partial"),
]


@pytest.fixture(scope="module", autouse=True)
def _require_reference():
    try:
        reference_path(UTIL)
    except ReferenceMissing as e:
        pytest.skip(str(e))


@pytest.mark.parametrize("case_id,args", ARG_CASES, ids=[i for i, _ in ARG_CASES])
def test_args(case_id, args):
    if case_id in SIGNATURE_CASE_IDS:
        assert_signature_match(UTIL, args)
    else:
        assert_match(UTIL, args)


@pytest.mark.parametrize("stdin", [s for _, s in STDIN_CASES], ids=[i for i, _ in STDIN_CASES])
def test_stdin(stdin):
    assert_match(UTIL, [], stdin)
