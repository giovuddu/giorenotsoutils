import pytest

from giore_golden import ReferenceMissing, measure_throughput, reference_path

UTIL = "yes"

THROUGHPUT_CASES: list[tuple[str, list[str]]] = [
    ("default", []),
    ("single-word", ["hello"]),
    ("multi-word", ["a", "b", "c"]),
    ("long-line", ["x" * 200]),
]


@pytest.fixture(scope="module", autouse=True)
def _require_reference():
    try:
        reference_path(UTIL)
    except ReferenceMissing as e:
        pytest.skip(str(e))


@pytest.mark.perf
@pytest.mark.parametrize(
    "case_id,args", THROUGHPUT_CASES, ids=[i for i, _ in THROUGHPUT_CASES]
)
def test_throughput(case_id, args):
    row = measure_throughput(UTIL, args, case_id=case_id)
    assert row["bin_mibps"] > 0
