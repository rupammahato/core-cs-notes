"""Publish S1 and advance only the next worked section to S2."""
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
    ' and [S0: URL shortener](/docs/system-design/url-shortener) |',
    ', [S0: URL shortener](/docs/system-design/url-shortener) and [S1: Rate limiter](/docs/system-design/rate-limiter) |')
replace(roadmap, 'S0 available; S1–S13 planned', 'S0 and S1 available; S2–S13 planned')
replace(roadmap, 'The site exposes this roadmap, A0–A4 and S0;',
    'The site exposes this roadmap, A0–A4, S0 and S1;')
replace(roadmap,
    '**Next: S1 — Rate limiter**, architecture part 8 / numeric module 6. It will develop window/token-bucket algorithms, atomic quota decisions and failure/degraded behavior.',
    'Continue with [S1: Rate limiter](/docs/system-design/rate-limiter) for window/token-bucket algorithms, atomic quota decisions and failure/degraded behavior. **Next: S2 — Notification and webhook delivery service**, architecture part 9 / numeric module 7. It will develop durable delivery attempts, signatures, retries, duplicate effects and provider limits.')
replace(roadmap, 'The roadmap, all foundations A0–A4 and S0 are authored in the new companion.',
    'The roadmap, all foundations A0–A4, S0 and S1 are authored in the new companion.')
replace('examples/system-design/roadmap/verify.py', "'checked_date':'2026-10-16'", "'checked_date':'2026-10-17'")
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['url-shortener'] },", "pages: ['url-shortener', 'rate-limiter'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan, '(roadmap, all foundations A0-A4 and S0 available; S1-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4, S0 and S1 available; S2-S13/consolidation planned)')
replace(plan, '- [ ] Remaining worked teaching chapters S1-S13 written.',
    '- [x] S1 rate limiter authored with 30 interview Q&As, ten exercises and 95 checks: eight algorithms, 16 validation, 14 bucket, 13 scope/lifecycle, seven concurrency, 26 HTTP, seven estimates and four cleanup. Includes window approximation counterexamples, atomic shared token decisions, four competing worker calls, clock/refill/cost boundaries, bounded state/reopen, real writer contention and explicit HTTP outage policies.\n- [ ] Remaining worked teaching chapters S2-S13 written.')
replace(plan, 'the roadmap, all foundations A0-A4 and S0 are published.',
    'the roadmap, all foundations A0-A4, S0 and S1 are published.')
replace(plan, 'Next: **S1: Rate limiter**, then S2-S13 and architecture consolidation.',
    'Next: **S2: Notification and webhook delivery service**, then S3-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0 are authored. Next: **S1: Rate limiter**.',
    'All foundations A0-A4, S0 and S1 are authored. Next: **S2: Notification and webhook delivery service**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,
    ' and [S0](/docs/system-design/url-shortener) available; remaining worked systems planned separately',
    ', [S0](/docs/system-design/url-shortener) and [S1](/docs/system-design/rate-limiter) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0 are available. Next planned section: **S1: Rate limiter**;',
    'The architecture roadmap, all foundations A0-A4, S0 and S1 are available. Next planned section: **S2: Notification and webhook delivery service**;')
replace('examples/system-design/module-5-url-shortener/author.py',
    '**Next: S1 — Rate limiter**, architecture part 8 / numeric module 6. It will develop fixed/sliding windows and token buckets, atomic shared decisions, quota keys/clocks and degraded behavior. S1 is planned and has no teaching route yet. S0 is the first authored worked system; remaining worked systems and consolidation continue one section at a time.',
    '**Next: [S1 — Rate limiter](/docs/system-design/rate-limiter)**, architecture part 8 / numeric module 6. It develops fixed/sliding windows and token buckets, atomic shared decisions, quota keys/clocks and degraded behavior, with its own local SQLite/HTTP verification scope. S0 and S1 are authored; remaining worked systems and consolidation continue one section at a time.')
for script in ('examples/system-design/module-5-url-shortener/author.py',
               'examples/system-design/roadmap/author.py', 'examples/system-design/roadmap/verify.py'):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/script)], cwd=ROOT,
        capture_output=True, text=True, encoding='utf-8', check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4, S0 URL shortener and S1 rate limiter: verified backend/data/cache/workflow/operations probes, link lifecycle and atomic quota decisions with clock/failure behavior; S2-S13/consolidation planned |', text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0 are available;',
    'the System Design roadmap, all foundations A0-A4, S0 and S1 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S2, notification and webhook delivery service.', text)
text = text.replace('architecture companion (roadmap, all foundations and S0 available)',
    'architecture companion (roadmap, all foundations, S0 and S1 available)')
readme.write_text(text, encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S2')
