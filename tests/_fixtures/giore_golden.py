from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = REPO_ROOT / "bin"
REFERENCE_DIR = Path("/usr/bin")

# not from os.environ: no host color/locale must leak into compared output
_STERILE_ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "LANG": "C"}


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: bytes
    stderr: bytes


class ReferenceMissing(Exception):
    pass


@cache
def reference_path(util: str) -> Path:
    p = REFERENCE_DIR / util
    if not p.exists():
        raise ReferenceMissing(
            f"No reference '{p}'. Run inside the test container: `make test`."
        )
    return p


def candidate_path(util: str) -> Path:
    return BIN_DIR / util


def _run(executable: Path, util: str, args: list[str], stdin: bytes) -> Result:
    proc = subprocess.run(
        [util, *args],            # argv[0] = basename, not the path
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


def _show(b: bytes, limit: int = 600, max_lines: int = 12) -> str:
    if b == b"":
        return repr(b)
    truncated = len(b) > limit
    s = b[:limit] if truncated else b
    try:
        text = s.decode("utf-8")
    except UnicodeDecodeError:
        return repr(s) + ("...<truncated>" if truncated else "")
    lines = text.split("\n")
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    block = "\n".join("      | " + line for line in lines)
    if truncated:
        block += "\n      | ...<truncated>"
    return "\n" + block


def _first_diff_offset(a: bytes, b: bytes) -> int | None:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    return None if len(a) == len(b) else n


def _results_match(ref: Result, cand: Result) -> bool:
    return (cand.returncode, cand.stdout, cand.stderr) == (
        ref.returncode, ref.stdout, ref.stderr
    )


def _raise_byte_divergence(
    util: str, args: list[str], input_desc: str, ref: Result, cand: Result
) -> None:
    lines = [
        "behavioural divergence",
        f"  util     : {util}",
        f"  argv     : {[util, *args]}",
        f"  input    : {input_desc}",
        "  --- exit code ---",
        f"    expected (GNU) : {ref.returncode}",
        f"    actual   (bin) : {cand.returncode}",
        "  --- stdout ---",
        f"    first differ at byte : {_first_diff_offset(ref.stdout, cand.stdout)}"
        f"  (len GNU={len(ref.stdout)}, bin={len(cand.stdout)})",
        f"    expected (GNU) : {_show(ref.stdout)}",
        f"    actual   (bin) : {_show(cand.stdout)}",
        "  --- stderr ---",
        f"    expected (GNU) : {_show(ref.stderr)}",
        f"    actual   (bin) : {_show(cand.stderr)}",
    ]
    raise AssertionError("\n".join(lines))


def assert_match(util: str, args: list[str], stdin: bytes = b"") -> None:
    ref = run_reference(util, args, stdin)
    cand = run_candidate(util, args, stdin)
    if not _results_match(ref, cand):
        _raise_byte_divergence(util, args, f"stdin={_show(stdin)}", ref, cand)


_CONTROL = frozenset(range(0x00, 0x20)) | {0x7f}


def _stream_signature(data: bytes) -> dict:
    n = len(data)
    lead = 0
    while lead < n and data[lead] in _CONTROL:
        lead += 1
    trail = 0
    while trail < n and data[n - 1 - trail] in _CONTROL:
        trail += 1
    # no line count: it tracks banner content, which drifts with version/packager
    return {
        "nonempty": n > 0,
        "ends_with_newline": data.endswith(b"\n"),
        "leading_control": lead,
        "trailing_control": trail,
    }


def _signature_diff(ref: dict, cand: dict, prefix: str = "") -> list[str]:
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
    return {
        "exit": r.returncode,
        "stdout": _stream_signature(r.stdout),
        "stderr": _stream_signature(r.stderr),
    }


def _raise_signature_divergence(
    util: str, args: list[str], input_desc: str,
    ref: Result, cand: Result, ref_sig: dict, cand_sig: dict,
) -> None:
    lines = [
        "structural-signature divergence",
        f"  util     : {util}",
        f"  argv     : {[util, *args]}",
        f"  input    : {input_desc}",
        "  --- differing fields ---",
        *_signature_diff(ref_sig, cand_sig),
        "  --- full signatures (context) ---",
        f"    GNU : {ref_sig}",
        f"    bin : {cand_sig}",
        "  --- raw output (context only) ---",
        f"    GNU stdout : {_show(ref.stdout)}",
        f"    bin stdout : {_show(cand.stdout)}",
        f"    GNU stderr : {_show(ref.stderr)}",
        f"    bin stderr : {_show(cand.stderr)}",
    ]
    raise AssertionError("\n".join(lines))


def assert_signature_match(util: str, args: list[str], stdin: bytes = b"") -> None:
    ref = run_reference(util, args, stdin)
    cand = run_candidate(util, args, stdin)
    ref_sig, cand_sig = output_signature(ref), output_signature(cand)
    if ref_sig != cand_sig:
        _raise_signature_divergence(
            util, args, f"stdin={_show(stdin)}", ref, cand, ref_sig, cand_sig
        )


STREAM_PREFIX_BYTES = 64 * 1024


def _run_stream(executable: Path, util: str, args: list[str], max_bytes: int) -> Result:
    proc = subprocess.Popen(
        [util, *args],            # argv[0] = basename, not the path
        executable=str(executable),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_STERILE_ENV,
    )
    out = bytearray()
    try:
        while len(out) < max_bytes:
            chunk = proc.stdout.read(min(65536, max_bytes - len(out)))
            if not chunk:
                break
            out.extend(chunk)
    finally:
        proc.stdout.close()       # writer gets SIGPIPE on next write
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    err = proc.stderr.read()
    proc.stderr.close()
    return Result(proc.returncode, bytes(out), err)


def run_reference_stream(util, args, max_bytes: int = STREAM_PREFIX_BYTES) -> Result:
    return _run_stream(reference_path(util), util, args, max_bytes)


def run_candidate_stream(util, args, max_bytes: int = STREAM_PREFIX_BYTES) -> Result:
    cand = candidate_path(util)
    if not cand.exists():
        raise FileNotFoundError(f"candidate '{cand}' not built — run `make`.")
    try:
        return _run_stream(cand, util, args, max_bytes)
    except OSError as e:
        raise AssertionError(
            f"candidate '{cand}' is not runnable ({e.strerror}); run `make`."
        ) from None


def assert_stream_match(
    util: str, args: list[str], max_bytes: int = STREAM_PREFIX_BYTES
) -> None:
    ref = run_reference_stream(util, args, max_bytes)
    cand = run_candidate_stream(util, args, max_bytes)
    if not _results_match(ref, cand):
        _raise_byte_divergence(util, args, f"stream first {max_bytes} bytes", ref, cand)


def assert_stream_signature(
    util: str, args: list[str], max_bytes: int = STREAM_PREFIX_BYTES
) -> None:
    ref = run_reference_stream(util, args, max_bytes)
    cand = run_candidate_stream(util, args, max_bytes)
    ref_sig, cand_sig = output_signature(ref), output_signature(cand)
    if ref_sig != cand_sig:
        _raise_signature_divergence(
            util, args, f"stream first {max_bytes} bytes", ref, cand, ref_sig, cand_sig
        )


# true/false: operands are ignored; same arg handling for both
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

# banner cases: content is ours by design -> signature, not bytes
SIGNATURE_CASE_IDS: frozenset[str] = frozenset({
    "help",
    "version",
    "help-then-version",
    "version-then-help",
})


# yes: operands ARE the output, streamed forever (space-joined + '\n')
YES_ARG_CASES: list[tuple[str, list[str]]] = [
    ("default", []),
    ("single-word", ["hello"]),
    ("multi-word", ["a", "b", "c"]),
    ("empty-string", [""]),
    ("dash-operand", ["-"]),
    ("double-dash-operand", ["--", "--help"]),
    ("special-chars", ["a\tb", "c d"]),
    ("unicode", ["café", "🚀"]),
    ("newline-operand", ["a\nb"]),
    ("many-words", ["w"] * 100),
    ("unknown-long", ["--bogus"]),
    ("unknown-short", ["-z"]),
    ("help", ["--help"]),
    ("version", ["--version"]),
    ("operand-then-help", ["foo", "--help"]),   # GNU permutes options -> help
    ("help-then-version", ["--help", "--version"]),
    ("version-then-help", ["--version", "--help"]),
]

YES_SIGNATURE_CASE_IDS: frozenset[str] = frozenset({
    "help",
    "version",
    "operand-then-help",
    "help-then-version",
    "version-then-help",
})


PERF_RESULTS: list[dict] = []
PERF_REPEATS = 15
PERF_WARMUP = 3


def _time_once(executable: Path, util: str, args: list[str], stdin: bytes) -> float:
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
    ref_exe = reference_path(util)
    cand = candidate_path(util)
    if not cand.exists():
        raise FileNotFoundError(f"candidate '{cand}' not built — run `make`.")

    for _ in range(warmup):
        _time_once(ref_exe, util, args, stdin)
        _time_once(cand, util, args, stdin)

    ref_t: list[float] = []
    cand_t: list[float] = []
    for _ in range(repeats):       # interleaved to dampen drift
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


THROUGHPUT_RESULTS: list[dict] = []
PERF_THROUGHPUT_BYTES = 64 * 1024 * 1024
PERF_THROUGHPUT_WARMUP = 8 * 1024 * 1024


def _drain(executable: Path, util: str, args: list[str], total_bytes: int) -> tuple[int, float]:
    proc = subprocess.Popen(
        [util, *args],
        executable=str(executable),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=_STERILE_ENV,
    )
    read = 0
    t0 = time.perf_counter()
    try:
        while read < total_bytes:
            chunk = proc.stdout.read(min(1 << 20, total_bytes - read))
            if not chunk:
                break
            read += len(chunk)
        dt = time.perf_counter() - t0
    finally:
        proc.stdout.close()
        proc.kill()
        proc.wait()
    return read, dt


def measure_throughput(
    util: str,
    args: list[str],
    case_id: str = "",
    total_bytes: int = PERF_THROUGHPUT_BYTES,
    warmup_bytes: int = PERF_THROUGHPUT_WARMUP,
) -> dict:
    ref_exe = reference_path(util)
    cand = candidate_path(util)
    if not cand.exists():
        raise FileNotFoundError(f"candidate '{cand}' not built — run `make`.")

    _drain(ref_exe, util, args, warmup_bytes)
    _drain(cand, util, args, warmup_bytes)

    ref_read, ref_dt = _drain(ref_exe, util, args, total_bytes)
    cand_read, cand_dt = _drain(cand, util, args, total_bytes)

    def mibps(n: int, dt: float) -> float:
        return (n / (1024 * 1024)) / dt if dt > 0 else float("inf")

    ref_mibps, cand_mibps = mibps(ref_read, ref_dt), mibps(cand_read, cand_dt)
    row = {
        "util": util,
        "case": case_id,
        "ref_mibps": ref_mibps,
        "bin_mibps": cand_mibps,
        "ratio": (ref_mibps / cand_mibps) if cand_mibps > 0 else float("inf"),
    }
    THROUGHPUT_RESULTS.append(row)
    return row


STDIN_CASES: list[tuple[str, bytes]] = [
    ("empty-stdin", b""),
    ("text-stdin", b"hello\nworld\n"),
    ("binary-stdin", bytes(range(256))),
    ("large-stdin", b"A" * (1 << 20)),
    ("no-trailing-newline", b"partial"),
]
