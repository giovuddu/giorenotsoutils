"""Pytest hooks shared across the test tree.

Renders the performance comparison (candidate vs GNU wall-clock) as a table in
the terminal summary. Behavioural pass/fail is unaffected; this only reports the
timings collected by ``measure_case``.
"""

from giore_golden import PERF_RESULTS


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if not PERF_RESULTS:
        return

    tr = terminalreporter
    tr.write_sep("=", "performance (wall-clock; median & min ms, ratio = bin/GNU)")
    header = (
        f"{'util':<6} {'case':<22} "
        f"{'GNU med':>8} {'bin med':>8} "
        f"{'GNU min':>8} {'bin min':>8} {'ratio':>7}"
    )
    tr.write_line(header)
    tr.write_line("-" * len(header))
    for r in sorted(PERF_RESULTS, key=lambda x: (x["util"], x["ratio"])):
        ratio = "inf" if r["ratio"] == float("inf") else f"{r['ratio']:.2f}x"
        tr.write_line(
            f"{r['util']:<6} {r['case']:<22} "
            f"{r['ref_ms']:>8.2f} {r['bin_ms']:>8.2f} "
            f"{r['ref_min_ms']:>8.2f} {r['bin_min_ms']:>8.2f} {ratio:>7}"
        )
