"""Shared helpers for live golden comparison tests.

A *golden* test runs the candidate ``bin/<util>`` AND the original GNU coreutil
side by side on identical input, then asserts behavioural parity. The GNU util
is the spec and is treated as a black box.

Everything runs inside a pinned ``debian:bookworm-slim`` container (see
``Dockerfile.test`` / ``docker-compose.test.yml``), so the reference is always
the system GNU coreutil at ``/usr/bin/<util>`` — no OS discrimination needed.

Both binaries are executed:
  - with ``argv[0]`` forced to the util's basename (e.g. ``"true"``): GNU embeds
    ``argv[0]`` in --help/error text, so without this the invocation path would
    leak into the output and produce spurious divergences;
  - in a STERILE, deterministic environment (``LC_ALL=C``, ``LANG=C``, minimal
    ``PATH``, and crucially NOT inheriting ``os.environ``), so stray
    ``COLORTERM`` / ``CLICOLOR`` / ``FORCE_COLOR`` or locale settings can't drift
    the compared output with ANSI/OSC-8 escapes.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = REPO_ROOT / "bin"
REFERENCE_DIR = Path("/usr/bin")

# Sterile, reproducible environment for every subprocess. Deliberately NOT built
# from os.environ: nothing from the host/container shell (color hints, locale)
# is allowed to leak into the output we compare.
_STERILE_ENV = {
    "PATH": "/usr/bin:/bin",
    "LC_ALL": "C",
    "LANG": "C",
}


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: bytes
    stderr: bytes


class ReferenceMissing(Exception):
    """Raised when the GNU reference coreutil is absent (not in the container)."""


@cache
def reference_path(util: str) -> Path:
    """The original GNU coreutil — always ``/usr/bin/<util>`` in the container.

    Memoized: the path is stable per util, resolved once.
    """
    p = REFERENCE_DIR / util
    if not p.exists():
        raise ReferenceMissing(
            f"No reference '{p}'. These tests must run inside the test "
            f"container (GNU coreutils installed): `make test-docker`."
        )
    return p


def candidate_path(util: str) -> Path:
    """Path to the author's compiled ``bin/<util>``."""
    return BIN_DIR / util


def _run(executable: Path, util: str, args: list[str], stdin: bytes) -> Result:
    proc = subprocess.run(
        [util, *args],            # argv[0] = basename, NOT the path
        executable=str(executable),
        input=stdin,
        capture_output=True,
        env=_STERILE_ENV,
        timeout=30,
    )
    return Result(proc.returncode, proc.stdout, proc.stderr)


def run_reference(util: str, args: list[str], stdin: bytes = b"") -> Result:
    return _run(reference_path(util), util, args, stdin)


def run_candidate(util: str, args: list[str], stdin: bytes = b"") -> Result:
    cand = candidate_path(util)
    if not cand.exists():
        raise FileNotFoundError(f"candidate '{cand}' not built — run `make`.")
    try:
        return _run(cand, util, args, stdin)
    except OSError as e:
        raise AssertionError(
            f"candidate '{cand}' is not runnable ({e.strerror}); run `make`."
        ) from None


def _show(b: bytes, limit: int = 600) -> str:
    """Render captured output for humans: decodable UTF-8 text is printed as an
    indented multi-line block (so help/version banners are readable); raw binary
    falls back to repr()."""
    if b == b"":
        return repr(b)
    truncated = len(b) > limit
    s = b[:limit] if truncated else b
    try:
        text = s.decode("utf-8")
    except UnicodeDecodeError:
        return repr(s) + ("...<truncated>" if truncated else "")
    block = "\n".join("      | " + line for line in text.split("\n"))
    if truncated:
        block += "\n      | ...<truncated>"
    return "\n" + block


# --- byte-for-byte golden comparison --------------------------------------
def assert_match(util: str, args: list[str], stdin: bytes = b"") -> None:
    """Assert full behavioural parity (stdout, stderr, exit) byte-for-byte."""
    ref = run_reference(util, args, stdin)
    cand = run_candidate(util, args, stdin)

    if (cand.returncode, cand.stdout, cand.stderr) == (
        ref.returncode, ref.stdout, ref.stderr
    ):
        return

    lines = [
        "behavioural divergence",
        f"  util     : {util}",
        f"  argv     : {[util, *args]}",
        f"  stdin    : {_show(stdin)}",
        "  --- exit code ---",
        f"    expected (GNU) : {ref.returncode}",
        f"    actual   (bin) : {cand.returncode}",
        "  --- stdout ---",
        f"    expected (GNU) : {_show(ref.stdout)}",
        f"    actual   (bin) : {_show(cand.stdout)}",
        "  --- stderr ---",
        f"    expected (GNU) : {_show(ref.stderr)}",
        f"    actual   (bin) : {_show(cand.stderr)}",
    ]
    raise AssertionError("\n".join(lines))


# --- structural signature (content-agnostic) ------------------------------
# Explicit control-byte set: C0 (0x00-0x1f) + DEL (0x7f). \t \n \r are part of
# C0 and ARE counted as control here — we want the *shape* (incl. ESC 0x1b and
# other non-whitespace control bytes), which a plain .strip() would miss.
_CONTROL = frozenset(range(0x00, 0x20)) | {0x7f}


def _stream_signature(data: bytes) -> dict:
    """Capture the FORM of one output stream, not its content.

    NOTE: deliberately NO line count. The number of lines is a proxy for the
    *content* of the banner and drifts with the GNU version / packager wording —
    exactly the thing these signature cases must ignore. We keep only hard,
    content-independent invariants below.
    """
    n = len(data)
    lead = 0
    while lead < n and data[lead] in _CONTROL:
        lead += 1
    trail = 0
    while trail < n and data[n - 1 - trail] in _CONTROL:
        trail += 1
    return {
        "nonempty": n > 0,
        "ends_with_newline": data.endswith(b"\n"),
        "leading_control": lead,
        "trailing_control": trail,  # includes the final \n
    }


def _signature_diff(ref: dict, cand: dict, prefix: str = "") -> list[str]:
    """Recursively list only the signature fields that differ, as
    ``field: GNU=... bin=...`` lines (dotted paths for nested streams)."""
    out: list[str] = []
    for key, ref_val in ref.items():
        path = f"{prefix}{key}"
        cand_val = cand.get(key)
        if isinstance(ref_val, dict) and isinstance(cand_val, dict):
            out += _signature_diff(ref_val, cand_val, f"{path}.")
        elif ref_val != cand_val:
            out.append(f"    {path}: GNU={ref_val!r} bin={cand_val!r}")
    return out


def output_signature(r: Result) -> dict:
    """Structural signature: exit code + per-stream shape (captures *which*
    stream carries output). Content (wording, version numbers) is ignored."""
    return {
        "exit": r.returncode,
        "stdout": _stream_signature(r.stdout),
        "stderr": _stream_signature(r.stderr),
    }


def assert_signature_match(util: str, args: list[str], stdin: bytes = b"") -> None:
    """Assert the candidate's output *shape* matches GNU's, deriving the expected
    signature live from the reference (never hardcoded).

    Use for cases whose textual content is ours by design (help/version banners):
    wording/version differ, but the form (stream, trailing newline, control
    framing, emptiness, exit code) must still match the GNU oracle.
    """
    ref = run_reference(util, args, stdin)
    cand = run_candidate(util, args, stdin)
    ref_sig = output_signature(ref)
    cand_sig = output_signature(cand)

    if cand_sig == ref_sig:
        return

    lines = [
        "structural-signature divergence",
        f"  util     : {util}",
        f"  argv     : {[util, *args]}",
        f"  stdin    : {_show(stdin)}",
        "  --- differing fields ---",
        *_signature_diff(ref_sig, cand_sig),
        "  --- full signatures (context) ---",
        f"    GNU : {ref_sig}",
        f"    bin : {cand_sig}",
        "  --- raw output (context only; content is NOT asserted) ---",
        f"    GNU stdout : {_show(ref.stdout)}",
        f"    bin stdout : {_show(cand.stdout)}",
        f"    GNU stderr : {_show(ref.stderr)}",
        f"    bin stderr : {_show(cand.stderr)}",
    ]
    raise AssertionError("\n".join(lines))


# --- shared case matrices -------------------------------------------------
# (id, argv-tail). true/false share identical argument handling.
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

# Explicit allowlist of arg-case ids whose stdout/stderr carry OUR OWN text
# (help/version banners), which diverges from GNU's wording/version numbers
# BY DESIGN. These use signature-match (structural FORM only). Every id NOT in
# this set is compared byte-for-byte against GNU. No clever filtering — if a
# case belongs here, list it explicitly with the reason above.
SIGNATURE_CASE_IDS: frozenset[str] = frozenset({
    "help",                 # our --help banner vs GNU usage text
    "version",              # our --version banner vs GNU version text
    "help-then-version",    # combined help/version: our banner content
    "version-then-help",    # combined help/version: our banner content
})

# --- performance comparison (wall-clock) ----------------------------------
# Each measured case is appended here and rendered as a table by the
# pytest_terminal_summary hook in tests/conftest.py.
PERF_RESULTS: list[dict] = []

PERF_REPEATS = 15   # measured samples per binary
PERF_WARMUP = 3     # discarded runs to prime caches / page-ins


def _time_once(executable: Path, util: str, args: list[str], stdin: bytes) -> float:
    """Wall-clock seconds for a single invocation (same sterile env as golden)."""
    t0 = time.perf_counter()
    subprocess.run(
        [util, *args],
        executable=str(executable),
        input=stdin,
        capture_output=True,
        env=_STERILE_ENV,
        timeout=30,
    )
    return time.perf_counter() - t0


def _median(xs: list[float]) -> float:
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def measure_case(
    util: str,
    args: list[str],
    stdin: bytes = b"",
    case_id: str = "",
    repeats: int = PERF_REPEATS,
    warmup: int = PERF_WARMUP,
) -> dict:
    """Measure candidate vs GNU wall-clock for one case, record and return a row.

    Reference and candidate are interleaved per sample to dampen drift (CPU
    frequency scaling, scheduler). We report the median (robust to outliers) and
    the min (least-noise floor). This is informational, not a hard assertion:
    true/false are dominated by process-spawn overhead, so timings are inherently
    noisy and not a pass/fail signal by themselves.
    """
    ref_exe = reference_path(util)
    cand = candidate_path(util)
    if not cand.exists():
        raise FileNotFoundError(f"candidate '{cand}' not built — run `make`.")

    for _ in range(warmup):
        _time_once(ref_exe, util, args, stdin)
        _time_once(cand, util, args, stdin)

    ref_t: list[float] = []
    cand_t: list[float] = []
    for _ in range(repeats):
        ref_t.append(_time_once(ref_exe, util, args, stdin))
        cand_t.append(_time_once(cand, util, args, stdin))

    ref_med, cand_med = _median(ref_t), _median(cand_t)
    row = {
        "util": util,
        "case": case_id,
        "ref_ms": ref_med * 1000,
        "bin_ms": cand_med * 1000,
        "ref_min_ms": min(ref_t) * 1000,
        "bin_min_ms": min(cand_t) * 1000,
        "ratio": (cand_med / ref_med) if ref_med > 0 else float("inf"),
    }
    PERF_RESULTS.append(row)
    return row


# (id, stdin-bytes) — true/false must never read or be affected by stdin.
STDIN_CASES: list[tuple[str, bytes]] = [
    ("empty-stdin", b""),
    ("text-stdin", b"hello\nworld\n"),
    ("binary-stdin", bytes(range(256))),
    ("large-stdin", b"A" * (1 << 20)),
    ("no-trailing-newline", b"partial"),
]
