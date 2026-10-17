"""Publish A4 and complete authored foundations, without marking worked systems complete."""
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
    file.write_text(text.replace(old,new),encoding='utf-8')


roadmap = 'examples/system-design/roadmap/author.py'
replace(roadmap,
    ' and [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency) |',
    ', [A3: Reliable workflows and concurrency](/docs/system-design/reliable-workflows-concurrency) and [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations) |')
replace(roadmap,'A0–A3 available; A4 planned','A0–A4 available; all five foundations authored')
replace(roadmap,'The site exposes this roadmap and A0–A3;','The site exposes this roadmap and A0–A4;')
replace(roadmap,
    '**Next: A4 — Operating a secure and observable system**, architecture part 6 / numeric module 4. It will connect permission boundaries, readiness/draining, telemetry, SLOs and capacity evidence.',
    'Finish the foundations with [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations). **Next: S0 — URL shortener**, architecture part 7 / numeric module 5. The first worked design will combine create/redirect contracts, unique codes, expiry, caching and bounded analytics.')
replace(roadmap,'The roadmap and A0–A3 are authored in the new companion.','The roadmap and A0–A4 are authored in the new companion.')
replace(roadmap,'A4, all worked systems and consolidation remain planned','All foundations are authored; all worked systems and consolidation remain planned')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling', 'reliable-workflows-concurrency']",
    "pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling', 'reliable-workflows-concurrency', 'secure-observable-operations']")
replace('Architecture-System-Design-Notes-Plan.md',
    '(roadmap and A0-A3 available; later chapters planned)',
    '(roadmap and all foundations A0-A4 available; worked systems/consolidation planned)')
replace('Architecture-System-Design-Notes-Plan.md',
    '- [ ] Foundation and worked teaching chapters written.',
    '- [x] A4 authored with 30 interview Q&As, ten exercises and 93 checks: 17 HTTP policy, 24 upload, seven quota, eleven lifecycle, five saturation, nine telemetry, two cleanup, thirteen offline-indicator and five hypothetical-planning assertions. Includes four owned loopback servers, current membership/scoped queries, private text quarantine, two-connection quota admission and drain/overload behavior; production identity/TLS, antivirus, orchestration and capacity remain outside scope.\n- [x] All five foundation teaching chapters A0-A4 authored.\n- [ ] Worked teaching chapters S0-S13 written.')
replace('Architecture-System-Design-Notes-Plan.md','the roadmap and A0-A3 are published.','the roadmap and all foundations A0-A4 are published.')
replace('Architecture-System-Design-Notes-Plan.md',
    'Next: **A4: Operating a secure and observable system**, then the worked designs beginning with S0.',
    'Next: **S0: URL shortener**, then S1-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'A0-A3 are authored. Next: **A4: Operating a secure and observable system**.',
    'All foundations A0-A4 are authored. Next: **S0: URL shortener**.')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    ' and [A3](/docs/system-design/reliable-workflows-concurrency) available;',
    ', [A3](/docs/system-design/reliable-workflows-concurrency) and [A4](/docs/system-design/secure-observable-operations) available;')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    'The architecture roadmap and A0-A3 are available. Next planned section: **A4: Operating a secure and observable system**;',
    'The architecture roadmap and all foundations A0-A4 are available. Next planned section: **S0: URL shortener**;')
replace('examples/system-design/module-3-reliable-workflows-concurrency/author.py',
    '**Next: A4 — Operating a secure and observable system**, architecture part 6 / numeric module 4. It will connect tenant scope, least privilege, quotas, safe uploads, readiness/draining, telemetry, SLOs and capacity evidence. A4 is planned and has no teaching route yet.',
    '**Next: [A4 — Operating a secure and observable system](/docs/system-design/secure-observable-operations)**, architecture part 6 / numeric module 4. It connects tenant scope, least privilege, quotas, safe uploads, readiness/draining, telemetry, SLOs and capacity evidence. A4 is now available with its own local HTTP and offline-indicator verification scope.')
for script in ('examples/system-design/module-3-reliable-workflows-concurrency/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,capture_output=True,
        text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap and all foundations A0-A4: design method, application/data boundaries, cache/scaling, reliable workflows, security/quotas/uploads, readiness/draining, telemetry/SLOs and explicit local verification; worked systems/consolidation planned |',text)
text = text.replace('the System Design roadmap and A0-A3 are available;',
                    'the System Design roadmap and all foundations A0-A4 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S0, URL shortener.',text)
text = text.replace('architecture companion (roadmap and A0-A3 available)',
                    'architecture companion (roadmap and all foundations available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; all foundations authored; next S0')
