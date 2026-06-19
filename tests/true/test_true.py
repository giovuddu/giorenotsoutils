import pytest

from giore_golden import (
    ARG_CASES,
    SIGNATURE_CASE_IDS,
    STDIN_CASES,
    ReferenceMissing,
    assert_match,
    assert_signature_match,
    reference_path,
)

UTIL = "true"


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
