from giore_golden import PERF_RESULTS, THROUGHPUT_RESULTS


def _perf_table(tr):
    if not PERF_RESULTS:
        return
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


def _throughput_table(tr):
    if not THROUGHPUT_RESULTS:
        return
    tr.write_sep("=", "throughput (streaming; MiB/s, ratio = GNU/bin, >1 = bin slower)")
    header = f"{'util':<6} {'case':<22} {'GNU MiB/s':>10} {'bin MiB/s':>10} {'ratio':>7}"
    tr.write_line(header)
    tr.write_line("-" * len(header))
    for r in sorted(THROUGHPUT_RESULTS, key=lambda x: (x["util"], -x["ratio"])):
        ratio = "inf" if r["ratio"] == float("inf") else f"{r['ratio']:.2f}x"
        tr.write_line(
            f"{r['util']:<6} {r['case']:<22} "
            f"{r['ref_mibps']:>10.1f} {r['bin_mibps']:>10.1f} {ratio:>7}"
        )


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    _perf_table(terminalreporter)
    _throughput_table(terminalreporter)
