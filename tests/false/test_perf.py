import pytest

from giore_golden import ARG_CASES, ReferenceMissing, measure_case, reference_path

UTIL = "false"


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
