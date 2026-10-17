"""Publish A3 while preserving original handbooks and leaving later chapters planned."""
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def replace(path, old, new):
    file = ROOT/path
    text = file.read_text(encoding='utf-8')
    if new in text:
        return
    assert old in text, (path, old)
    file.write_text(text.replace(old, new), encoding='utf-8')


roadmap = 'examples/system-design/roadmap/author.py'
replace(roadmap,
    ' and [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling) |',
    ', [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling) and [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency) |')
replace(roadmap, 'A0–A2 available; A3–A4 planned', 'A0–A3 available; A4 planned')
replace(roadmap, 'The site exposes this roadmap and A0–A2;', 'The site exposes this roadmap and A0–A3;')
replace(roadmap,
    '**Next: A3 — Reliable workflows and concurrency**, architecture part 5 / numeric module 3. It will develop bounded retries, durable delivery, operation identity and recovery.',
    'Continue with [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency). **Next: A4 — Operating a secure and observable system**, architecture part 6 / numeric module 4. It will connect permission boundaries, readiness/draining, telemetry, SLOs and capacity evidence.')
replace(roadmap, 'The roadmap and A0–A2 are authored in the new companion.', 'The roadmap and A0–A3 are authored in the new companion.')
replace(roadmap, 'A3–A4, all worked systems and consolidation remain planned', 'A4, all worked systems and consolidation remain planned')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling']",
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling', 'reliable-workflows-concurrency']")
replace('Architecture-System-Design-Notes-Plan.md',
    '(roadmap and A0-A2 available; later chapters planned)', '(roadmap and A0-A3 available; later chapters planned)')
replace('Architecture-System-Design-Notes-Plan.md',
    '- [ ] Foundation and worked teaching chapters written.',
    '- [x] A3 authored with 30 interview Q&As, ten exercises and 90 checks: 19 retry-policy, 14 atomic-operation, ten lease, twelve consumer-atomicity, eleven delivery-bound, ten concurrency, twelve compensation and two cleanup assertions. Includes real SQLite outbox/inbox recovery, six competing worker calls, bounded claim generations and guarded local compensation; network/provider/broker/full-saga behavior remains outside scope.\n- [ ] Foundation and worked teaching chapters written.')
replace('Architecture-System-Design-Notes-Plan.md', 'the roadmap and A0-A2 are published.', 'the roadmap and A0-A3 are published.')
replace('Architecture-System-Design-Notes-Plan.md',
    'Next: **A3: Reliable workflows and concurrency**, then A4 and the worked designs beginning with S0.',
    'Next: **A4: Operating a secure and observable system**, then the worked designs beginning with S0.')
replace('Resume-Skills-Notes-Plan.md',
    'A0-A2 are authored. Next: **A3: Reliable workflows and concurrency**.',
    'A0-A3 are authored. Next: **A4: Operating a secure and observable system**.')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    ' and [A2](/docs/system-design/data-caching-scaling) available;',
    ', [A2](/docs/system-design/data-caching-scaling) and [A3](/docs/system-design/reliable-workflows-concurrency) available;')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    'The architecture roadmap and A0-A2 are available. Next planned section: **A3: Reliable workflows and concurrency**;',
    'The architecture roadmap and A0-A3 are available. Next planned section: **A4: Operating a secure and observable system**;')
replace('examples/system-design/module-2-data-caching-scaling/author.py',
    '**Next: A3 — Reliable workflows and concurrency**, architecture part 5 / numeric module 3. It will develop bounded retries, operation identity, constraints/versions/locks, durable delivery, outbox and recovery/compensation. A3 is planned and has no teaching route yet.',
    '**Next: [A3 — Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency)**, architecture part 5 / numeric module 3. It develops bounded retries, operation identity, constraints/versions/locks, durable delivery, outbox and recovery/compensation. A3 is now available with its own local transaction/recovery verification scope.')
for script in ('examples/system-design/module-2-data-caching-scaling/author.py',
               'examples/system-design/roadmap/author.py', 'examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/script)], cwd=ROOT, capture_output=True,
        text=True, encoding='utf-8', check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap and A0-A3: design method, application boundaries, data/cache/scaling, verified backend and SQLite probes, bounded retries, outbox/inbox recovery, competing writes, leases and compensation; final foundation/worked systems planned |', text)
text = text.replace('the System Design roadmap and A0-A2 are available;', 'the System Design roadmap and A0-A3 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: A4, operating a secure and observable system.', text)
text = text.replace('architecture companion (roadmap and A0-A2 available)', 'architecture companion (roadmap and A0-A3 available)')
readme.write_text(text, encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next A4')
