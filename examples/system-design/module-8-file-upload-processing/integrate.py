"""Publish S3 while retaining planned status for the remaining worked systems."""
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
    assert old in text, (path,old)
    file.write_text(text.replace(old,new),encoding='utf-8')


roadmap = 'examples/system-design/roadmap/author.py'
replace(roadmap,
    ' and [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) |',
    ', [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) and [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing) |')
replace(roadmap, 'S0, S1 and S2 available; S3–S13 planned', 'S0–S3 available; S4–S13 planned')
replace(roadmap, 'The site exposes this roadmap, A0–A4 and S0–S2;',
    'The site exposes this roadmap, A0–A4 and S0–S3;')
replace(roadmap,
    '**Next: S3 — File upload, storage and processing service**, architecture part 10 / numeric module 8. It will develop metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup.',
    'Continue with [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing) for metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup. **Next: S4 — Ticket booking and limited-inventory reservation**, architecture part 11 / numeric module 9. It will develop authoritative inventory, atomic holds, expiry, concurrent booking attempts and late-payment decisions.')
replace(roadmap, 'The roadmap, all foundations A0–A4 and S0–S2 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S3 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks'] },",
    "pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks', 'file-upload-processing'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan, '(roadmap, all foundations A0-A4 and S0-S2 available; S3-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S3 available; S4-S13/consolidation planned)')
replace(plan, '- [ ] Remaining worked teaching chapters S3-S13 written.',
    '- [x] S3 file upload/storage/processing authored with 30 interview Q&As, ten exercises and 121 checks: 17 validation, 23 intake, 19 processing, 19 lifecycle, 27 HTTP, four concurrency, eight estimates and four cleanup. Includes scoped create replay/capabilities, immutable real files, atomic completion/job, quarantine, guarded worker publication, delete/expiry, orphan reconciliation and private download. Six competing PUT/completion/claim calls and actual artifact-after-metadata-rollback recovery are verified locally; cloud multipart and antivirus remain explicitly unimplemented.\n- [ ] Remaining worked teaching chapters S4-S13 written.')
replace(plan, 'the roadmap, all foundations A0-A4 and S0-S2 are published.',
    'the roadmap, all foundations A0-A4 and S0-S3 are published.')
replace(plan, 'Next: **S3: File upload, storage and processing service**, then S4-S13 and architecture consolidation.',
    'Next: **S4: Ticket booking and limited-inventory reservation**, then S5-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0-S2 are authored. Next: **S3: File upload, storage and processing service**.',
    'All foundations A0-A4 and S0-S3 are authored. Next: **S4: Ticket booking and limited-inventory reservation**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,
    ' and [S2](/docs/system-design/notifications-webhooks) available; remaining worked systems planned separately',
    ', [S2](/docs/system-design/notifications-webhooks) and [S3](/docs/system-design/file-upload-processing) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S2 are available. Next planned section: **S3: File upload, storage and processing service**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S3 are available. Next planned section: **S4: Ticket booking and limited-inventory reservation**;')
replace('examples/system-design/module-7-notifications-webhooks/author.py',
    '**Next: S3 — File upload, storage and processing service**, architecture part 10 / numeric module 8. It will develop metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup. S3 is planned and has no teaching route yet. Continue one section at a time; remaining worked systems and architecture consolidation remain planned.',
    '**Next: [S3 — File upload, storage and processing service](/docs/system-design/file-upload-processing)**, architecture part 10 / numeric module 8. It develops metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup, with its own immutable local-file/SQLite/HTTP verification scope. S0-S3 are authored; remaining worked systems and architecture consolidation continue one section at a time.')
for script in ('examples/system-design/module-7-notifications-webhooks/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S3: URL shortener, atomic rate limiter, durable webhook delivery and immutable file upload/processing with failure/cleanup verification; S4-S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S2 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S3 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S4, ticket booking and limited-inventory reservation.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S2 available)',
    'architecture companion (roadmap, all foundations and S0-S3 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S4')
