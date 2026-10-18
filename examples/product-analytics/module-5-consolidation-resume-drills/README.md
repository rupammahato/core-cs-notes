# P5 final revision companion

Twelve isolated output drills plus source and curriculum audits. The outputs are teaching evidence, not original project behavior, hiring prediction or a grade for your spoken answers.

From the repository root:

```powershell
python examples/product-analytics/module-5-consolidation-resume-drills/verify.py
```

Python standard library only. Verified with Python 3.13.15 and SQLite 3.50.4: **27 checks**, consisting of **12 isolated outputs** and **15 source/coverage audits**. Every drill runs in a separate Python process with a timeout; the runner checks its actual JSON against independently specified expected-output.json. All workers exit. D07 closes a real in-memory SQLite connection.

D01-D03 execute the prior P0/P1 helpers and D10-D11 execute the P4 local functions. Other drills use small standard-library examples. This does not re-run the complete historical NumPy/pandas, native Excel or D3 suites, and does not change their recorded runtime versions.

The 15 audits cover six canonical chapter mappings, seven projects in both source entries of the existing M28 resume catalogue, and two local PDF fingerprints. The full audit expects both original local PDFs; they remain ignored and are not distributed with the repository. Individual drill files can run separately without those PDFs. The audits establish coverage and source correspondence, not independent verification of historical implementation or business impact. Contact details are not copied into this companion.

coverage.json maps P0-P5 to their authored files and routes. story-map.json preserves seven project identities with resume-reported evidence labels. drill-output.json records executed results; verification-results.json records checks, worker exits, source fingerprints and dependency preservation.

research.json records two primary interview-preparation sources and the internal consolidation boundary. validate_content.py checks the final chapter, all product links, current availability, manual-work labels, old-source preservation and track counts. site-smoke.mjs validates the production build's routes, navigation, all six product chapters and scoped search using an automatically closed temporary loopback preview. Port 3000 remains stopped.

The chapter contains seven story cards, 30 confusable pairs, 16 diagnosis cards, 60 rapid-fire Q&As, two 45-minute mocks, 12 practice tasks, a 24-question self-test and revision schedules. These are editorial learner exercises. Story accuracy, original outcome corroboration, manual accessibility/PivotTable practice and personal interview delivery require your own work.
