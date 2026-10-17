# Final architecture consolidation

`lesson.md` and `answers.json` author the final revision material: 60 expanded bank drills, 14 failure cards, 24 confusable pairs, 24 self-tests, six 45-minute mocks and revision routes. `revision.py` accepts manually supplied 0–3 scores; it does not grade answers or predict readiness. `--demo` uses synthetic input, and default output is a blank worksheet.

`author.py` generates Part 21 and `catalogue.json`, covering all 19 teaching chapters with exact chapter/proof hashes, source paths, original runtimes/dates and 1,600 recorded assertions. It requires the authored S13 files. `verify.py` performs 204 fresh document/provenance/helper checks; it audits historical receipts without rerunning their original engines. No learner checklist is automatically checked.

From repository root:

```powershell
python examples/system-design/consolidation/revision.py --demo
python examples/system-design/consolidation/verify.py
```

After editing sources or rerunning teaching verifiers, regenerate with the final workflow in `../finish-track/README.md` so catalogue hashes stay current. No server, paid service or Docker is needed for these scripts.
