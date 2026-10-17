# A0: How to approach a design question

Run `python verify.py` with Python 3.12 or later. The recorded run uses Python 3.12.10 and SQLite 3.49.1; no third-party packages, Docker or cloud credentials are required.

- `estimates.py`: hypothetical requests/storage/response-bandwidth/capacity arithmetic and sensitivity. Capacity, retention and physical-copy inputs are assumptions, not measured/implemented properties.
- `objectives.py`: offline classification of hand-authored eligible/good events plus a separate invariant gate. No traffic collection or production SLO result.
- `baseline.py`: a persistent private-note repository probe with scoped resource queries, versioned replacement and transactional create-operation outcomes. It accepts supplied identities; it does not authenticate them or serve HTTP.
- `verify.py`: 62 named checks (23 arithmetic/input, 12 offline objective, 23 repository and four concurrent invariant checks), using temporary SQLite files and four completed worker calls across two concurrent pairs.
- `author.py`: chapter generator with three exact sources and four recorded observation blocks.
- `validate_site.py`: fidelity, build, navigation, route/search and cleanup checks on an owned temporary site preview.

The probe closes connections before removing its temporary data, including on failure paths. Its fault-injection argument is internal fixture tooling, not a public request field. The HTTP/ETag/status mapping and deployment/authentication diagrams in the chapter are proposed contracts, not executed service behavior.

No load/latency benchmark, hosted service, payment/provider/model call or persistent model listener runs. The site preview closes after validation and port 3000 remains stopped. A1 supplies the next application-boundary/framework chapter.
