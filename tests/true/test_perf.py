"""Performance comparison: bin/true vs GNU true (wall-clock).

Informational, not a speed gate (true is spawn-dominated → noisy). Results are
printed as a table in the terminal summary. Run only these with `-m perf`,
or skip them with `-m "not perf"`.
"""

import pytest

from giore_golden import ARG_CASES, ReferenceMissing, measure_case, reference_path

UTIL = "true"


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
    assert row["bin_ms"] >= 0  # recorded; speed is reported, not asserted
