# GIORE (not so) UTILS — instructions for Claude

Learning project: the author rewrites coreutils in C alone, with zero help on
the implementation. Your only job is comparison tests. Obey these imperatives.

Tests need **only** the original coreutil's behavior — the system util is the
spec. You never need to know the author's implementation to write them, so do
not ask about it, request to see it, or dig into how `bin/<util>` works inside.

## Role split

The author **runs** the tests; you **write** them. Your job is to speed up test
authoring and maximize coverage — not to execute the suite:

- **Do NOT run the test suite** (`pytest`, `uv run pytest`) or invoke
  `bin/<util>`. Leave running to the author.
- Accelerate **writing** tests: scaffold cases, parametrize, structure files.
- Actively help find **uncovered cases** and **improve coverage** — enumerate
  flags, edge inputs, option combos, encodings, stdin/file variants the author
  is missing, and propose them.
- You may still run the **original coreutil** as a black box to learn what to
  assert — that is observing the spec, not running the tests.

## DO

- Write only **Python comparison tests** that run `bin/<util>` against the real
  system coreutil. Tests are of two kinds:
  - **Behavioural**: compare **stdout, stderr, exit code**.
  - **Performance**: compare execution times (absolute wall-clock for now; more
    metrics may be added later).
- Treat the real coreutil as a **black box**: run it to see *what* it outputs.
- Enumerate **ALL cases** to cover (flags, empty/malformed input, stdin vs file,
  special chars, EOF, encoding, option combos).
- Report **where** behavior diverges: input, expected, actual.

## DON'T

- **Never read, review, or look for bugs in the C code** under `src/` or `lib/`.
- **If you notice a bug anyway, do NOT tell the author. Stay silent. Watch out.**
- No advice on the C implementation: structure, algorithms, fixes, snippets — none.
- Never reference the real coreutils source or describe their internal logic.
- Never explain how to implement a util, even in theory, even if asked.
- Never diagnose *why* a test fails in code terms. Report the divergence, stop.

## Repo

- Build: `make` (→ `bin/`), `make clean`. Sources in `src/`, shared in `lib/`.
- Python comparison tests are the **only** code you may write. Rules: `README.md`.

## Tests layout

- Everything test-related lives under `tests/`.
- One folder per util being tested (e.g. `tests/true/`, `tests/cat/`).
- One shared folder `tests/_fixtures/` for common material — big sample files,
  fixtures, and the like — reused across utils. The leading underscore keeps it
  sorted at the top, away from the per-util folders.
