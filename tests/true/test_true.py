"""Golden comparison: bin/true vs GNU true (live)."""

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
    """No GNU reference → skip (not fail): nothing to compare against here."""
    try:
        reference_path(UTIL)
    except ReferenceMissing as e:
        pytest.skip(str(e))


@pytest.mark.parametrize(
    "case_id,args", ARG_CASES, ids=[i for i, _ in ARG_CASES]
)
def test_args(case_id, args):
    # help/version banners carry our own text → compare structural signature.
    # All other cases must match GNU byte-for-byte.
    if case_id in SIGNATURE_CASE_IDS:
        assert_signature_match(UTIL, args)
    else:
        assert_match(UTIL, args)


@pytest.mark.parametrize("stdin", [s for _, s in STDIN_CASES], ids=[i for i, _ in STDIN_CASES])
def test_stdin(stdin):
    assert_match(UTIL, [], stdin)
