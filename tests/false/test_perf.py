import pytest

from harness import ReferenceMissing, measure_case, reference_path

UTIL = "false"

# Same invocation shapes as the behavioural suite: here we time startup + arg
# parsing on each form (true/false ignore operands, so this is startup cost).
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


@pytest.fixture(scope="module", autouse=True)
def _require_reference():
    try:
        reference_path(UTIL)
    except ReferenceMissing as e:
        pytest.skip(str(e))


@pytest.mark.perf
@pytest.mark.parametrize("case_id,args", ARG_CASES, ids=[i for i, _ in ARG_CASES])
def test_perf(case_id, args):
    row = measure_case(UTIL, args, case_id=case_id)
    assert row["bin_ms"] >= 0
