import pytest

from giore_golden import (
    YES_ARG_CASES,
    YES_SIGNATURE_CASE_IDS,
    ReferenceMissing,
    assert_stream_match,
    assert_stream_signature,
    reference_path,
)

UTIL = "yes"


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
