"""Publish only the completed A2 chapter and update the next section to A3."""
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
    ' and [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries) |',
    ', [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries) and [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling) |')
replace(roadmap, 'A0 and A1 available; A2–A4 planned', 'A0–A2 available; A3–A4 planned')
replace(roadmap, 'The site exposes this roadmap, A0 and A1;', 'The site exposes this roadmap and A0–A2;')
replace(roadmap,
    '**Next: A2 — Data, caching and scaling**, architecture part 4 / numeric module 2. It will connect access patterns and consistency requirements to data and scaling choices.',
    'Continue with [A2: Data, caching and scaling](/docs/system-design/data-caching-scaling). **Next: A3 — Reliable workflows and concurrency**, architecture part 5 / numeric module 3. It will develop bounded retries, durable delivery, operation identity and recovery.')
replace(roadmap, 'The roadmap, A0 and A1 are authored in the new companion.', 'The roadmap and A0–A2 are authored in the new companion.')
replace(roadmap, 'A2–A4, all worked systems and consolidation remain planned', 'A3–A4, all worked systems and consolidation remain planned')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries']",
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling']")
replace('Architecture-System-Design-Notes-Plan.md',
    '(roadmap, A0 and A1 available; later chapters planned)', '(roadmap and A0-A2 available; later chapters planned)')
replace('Architecture-System-Design-Notes-Plan.md',
    '- [ ] Foundation and worked teaching chapters written.',
    '- [x] A2 authored with 30 interview Q&As, ten exercises and 91 checks: 12 query/index, 16 pagination, 23 basic cache, ten single-flight, eleven invalidation, four independent-cache, two cleanup and thirteen hypothetical scaling-model checks. Includes real SQLite plans/VM work, offset drift, scoped TTL/LRU, stale-refill reproduction and local fencing; distributed replicas/shards/Redis and capacity remain explanatory.\n- [ ] Foundation and worked teaching chapters written.')
replace('Architecture-System-Design-Notes-Plan.md',
    'the roadmap, A0 and A1 are published.', 'the roadmap and A0-A2 are published.')
replace('Architecture-System-Design-Notes-Plan.md',
    'Next: **A2: Data, caching and scaling**, then A3-A4 and the worked designs beginning with S0.',
    'Next: **A3: Reliable workflows and concurrency**, then A4 and the worked designs beginning with S0.')
replace('Resume-Skills-Notes-Plan.md',
    'A0 and A1 are authored. Next: **A2: Data, caching and scaling**.',
    'A0-A2 are authored. Next: **A3: Reliable workflows and concurrency**.')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    ' and [A1](/docs/system-design/application-architecture-service-boundaries) available;',
    ', [A1](/docs/system-design/application-architecture-service-boundaries) and [A2](/docs/system-design/data-caching-scaling) available;')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    'The architecture roadmap, A0 and A1 are available. Next planned section: **A2: Data, caching and scaling**;',
    'The architecture roadmap and A0-A2 are available. Next planned section: **A3: Reliable workflows and concurrency**;')
replace('examples/system-design/module-1-application-architecture/author.py',
    '**Next: A2 — Data, caching and scaling**, architecture part 4 / numeric module 2. It will connect access patterns and consistency requirements to indexes, replicas/shards, caches, hot keys and scaling choices. A2 is planned and has no teaching route yet.',
    '**Next: [A2 — Data, caching and scaling](/docs/system-design/data-caching-scaling)**, architecture part 4 / numeric module 2. It connects access patterns and consistency requirements to indexes, replicas/shards, caches, hot keys and scaling choices. A2 is now available with its own local data/cache verification scope.')
for script in ('examples/system-design/module-1-application-architecture/author.py',
               'examples/system-design/roadmap/author.py', 'examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/script)], cwd=ROOT, capture_output=True,
        text=True, encoding='utf-8', check=True)
    print(script+': OK')
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap and A0-A2: design method, application boundaries, verified TypeScript/Express backend, real SQLite query plans/pagination, cache freshness/races and scaling trade-offs; remaining foundations/worked systems planned |', text)
text = text.replace('the System Design roadmap, A0 and A1 are available;', 'the System Design roadmap and A0-A2 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: A3, reliable workflows and concurrency.', text)
text = text.replace('architecture companion (roadmap, A0 and A1 available)', 'architecture companion (roadmap and A0-A2 available)')
readme.write_text(text, encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next A3')
