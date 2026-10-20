# Machine coding practice

Eight single-threaded C++17 exercises accompany the eleven chapters in `Machine Coding Notes/`.
The notes contain the authored explanations; `build_book.py` replaces only marked source and transcript blocks.

From the repository root, with Python 3 and a C++17 g++ compiler on PATH:

```powershell
python examples/machine-coding/verify.py
python examples/machine-coding/verify.py --trace T01
python examples/machine-coding/build_book.py
python examples/machine-coding/validate_content.py
```

The verifier compiles `main.cpp` and `api_tests.cpp` with warnings as errors.
It checks 32 authored traces, malformed commands, numeric boundaries, direct callback APIs and seeded reference histories for all eight exercises.
`verification-results.json` records the actual group and command counts, compiler, flags and source hashes.
`observations.json` contains exact outputs inserted into the notes; `compile-output.json` contains compiler commands and diagnostics.
Executables are local and ignored under `.build/`; they are not source artifacts to commit.

Modes: `kv`, `limiter`, `bus`, `scheduler`, `vending`, `booking`, `search`, `flags`.
Run `.build/machines.exe <mode>` on Windows, or `.build/machines <mode>` on other platforms, and send one command per line.
See the harness chapter for exact commands, quote syntax, limits and output schema.
Each process starts fresh. The trace option requires the runner to have been compiled first.

Reference strategies differ where useful: accepted-log scans, sorted jobs, occupied slots, full-text scans and exhaustive bounded change.
The vending oracle accepts any feasible returned coin combination and checks its availability/value rather than imposing the DP's tie break.
The tests use finite histories with seed 20261021. No concurrency, crash recovery, allocation-failure injection, sanitizer or performance benchmark is claimed.

`research.json` lists primary sources and distinguishes editorial exercise contracts from employer guidance.
`prior-notes-snapshot.json` protects all 163 pre-existing handbook files byte for byte.
`content-validation.json` records authored coverage and exact code/transcript checks.

Website validation runs after sync and production build:

```powershell
node examples/machine-coding/site-smoke.mjs
```

The smoke script chooses a temporary loopback port other than 3000, checks all 175 page routes, new content, sidebar/home card and scoped search, then closes its own server.
`site-build-output.txt` records the production build. In this restricted environment the build uses the existing local Google-font response fixture via `NEXT_FONT_GOOGLE_MOCKED_RESPONSES`; the site's normal font configuration is unchanged.
`site-validation.json` and `validation-summary.json` record the final observed results, without claiming a visual browser review.
