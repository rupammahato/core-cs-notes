"""Publish S2 while keeping later worked designs explicitly planned."""
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
    ' and [S1: Rate limiter](/docs/system-design/rate-limiter) |',
    ', [S1: Rate limiter](/docs/system-design/rate-limiter) and [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) |')
replace(roadmap, 'S0 and S1 available; S2–S13 planned', 'S0, S1 and S2 available; S3–S13 planned')
replace(roadmap, 'The site exposes this roadmap, A0–A4, S0 and S1;',
    'The site exposes this roadmap, A0–A4 and S0–S2;')
replace(roadmap,
    '**Next: S2 — Notification and webhook delivery service**, architecture part 9 / numeric module 7. It will develop durable delivery attempts, signatures, retries, duplicate effects and provider limits.',
    'Continue with [S2: Notification and webhook delivery service](/docs/system-design/notifications-webhooks) for durable delivery attempts, signatures, retries, duplicate effects and provider limits. **Next: S3 — File upload, storage and processing service**, architecture part 10 / numeric module 8. It will develop metadata/object boundaries, upload authorization/completion, validation/quarantine, asynchronous processing and cleanup.')
replace(roadmap, 'The roadmap, all foundations A0–A4, S0 and S1 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S2 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['url-shortener', 'rate-limiter'] },",
    "pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan, '(roadmap, all foundations A0-A4, S0 and S1 available; S2-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S2 available; S3-S13/consolidation planned)')
replace(plan, '- [ ] Remaining worked teaching chapters S2-S13 written.',
    '- [x] S2 notification/webhook delivery authored with 30 interview Q&As, ten exercises and 109 checks: 11 validation, 17 intake, four concurrency, 16 leases, 13 retry, 22 HTTP, 14 network, eight estimates and four cleanup. Includes atomic event/fan-out, original-intent replay, preferences, competing claims, lease fencing/crash budgets, shared 429 cooldowns, raw-byte HMAC, receiver receipt/effect rollback and actual connection loss after commit followed by duplicate-safe retry. Six concurrent worker/request calls use owned local fixtures.\n- [ ] Remaining worked teaching chapters S3-S13 written.')
replace(plan, 'the roadmap, all foundations A0-A4, S0 and S1 are published.',
    'the roadmap, all foundations A0-A4 and S0-S2 are published.')
replace(plan, 'Next: **S2: Notification and webhook delivery service**, then S3-S13 and architecture consolidation.',
    'Next: **S3: File upload, storage and processing service**, then S4-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4, S0 and S1 are authored. Next: **S2: Notification and webhook delivery service**.',
    'All foundations A0-A4 and S0-S2 are authored. Next: **S3: File upload, storage and processing service**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume, ' and [S1](/docs/system-design/rate-limiter) available; remaining worked systems planned separately',
    ', [S1](/docs/system-design/rate-limiter) and [S2](/docs/system-design/notifications-webhooks) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4, S0 and S1 are available. Next planned section: **S2: Notification and webhook delivery service**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S2 are available. Next planned section: **S3: File upload, storage and processing service**;')
replace('examples/system-design/module-6-rate-limiter/author.py',
    '**Next: S2 — Notification and webhook delivery service**, architecture part 9 / numeric module 7. It will develop durable delivery attempts, preferences, provider limits, signatures, retries and duplicate-effect handling. S2 is planned and has no teaching route yet. Continue one section at a time; remaining worked systems and architecture consolidation remain planned.',
    '**Next: [S2 — Notification and webhook delivery service](/docs/system-design/notifications-webhooks)**, architecture part 9 / numeric module 7. It develops durable delivery attempts, preferences, provider limits, signatures, retries and duplicate-effect handling, with its own local SQLite/signed-HTTP verification scope. S0-S2 are authored; remaining worked systems and architecture consolidation continue one section at a time.')
for script in ('examples/system-design/module-6-rate-limiter/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S2: URL shortener, atomic rate limiter and durable signed notification/webhook delivery with failure/retry verification; S3-S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4, S0 and S1 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S2 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S3, file upload, storage and processing service.',text)
text = text.replace('architecture companion (roadmap, all foundations, S0 and S1 available)',
    'architecture companion (roadmap, all foundations and S0-S2 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S3')
