import pytest

from harness import ReferenceMissing, measure_throughput, reference_path

UTIL = "yes"

THROUGHPUT_CASES: list[tuple[str, list[str]]] = [
    ("default", []),
    ("single-word", ["hello"]),
    ("multi-word", ["a", "b", "c"]),
    ("long-line", ["x" * 200]),
]

# Curva: stessa forma (un solo argomento), lunghezza riga su scala log.
# Mappa come scala il ratio rispetto alla dimensione della riga emessa.
THROUGHPUT_CASES += [
    (f"line-{n}b", ["x" * n]) for n in (1, 4, 16, 64, 256, 1024, 4096)
]

# Asse ortogonale: stessi byte per riga (~99), ma "tanti token corti" contro
# "un token lungo". Separa il costo-per-argomento dal costo-per-byte.
THROUGHPUT_CASES += [
    ("many-short-args", ["a"] * 50),  # riga "a a a ... a" (~99 byte)
    ("one-long-arg", ["a" * 99]),     # riga "aaa...a"     (~99 byte)
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
