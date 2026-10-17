"""Publish the first worked system without claiming later designs are complete."""
from pathlib import Path
import re
import subprocess
import sys

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]


def replace(path,old,new):
    file=ROOT/path
    text=file.read_text(encoding='utf-8')
    if new in text:
        return
    assert old in text,(path,old)
    file.write_text(text.replace(old,new),encoding='utf-8')


roadmap='examples/system-design/roadmap/author.py'
replace(roadmap,
    ' and [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations) |',
    ', [A4: Operating a secure and observable system](/docs/system-design/secure-observable-operations) and [S0: URL shortener](/docs/system-design/url-shortener) |')
replace(roadmap,'| Worked systems S0–S13 | Planned; not yet implemented in this companion |',
    '| Worked systems S0–S13 | S0 available; S1–S13 planned |')
replace(roadmap,'The site exposes this roadmap and A0–A4;',
    'The site exposes this roadmap, A0–A4 and S0;')
replace(roadmap,'| Worked implementations and their failure evidence | Planned |',
    '| Worked implementations and their failure evidence | S0 available; S1–S13 planned |')
replace(roadmap,
    '**Next: S0 — URL shortener**, architecture part 7 / numeric module 5. The first worked design will combine create/redirect contracts, unique codes, expiry, caching and bounded analytics.',
    'Continue with [S0: URL shortener](/docs/system-design/url-shortener), the first worked design. **Next: S1 — Rate limiter**, architecture part 8 / numeric module 6. It will develop window/token-bucket algorithms, atomic quota decisions and failure/degraded behavior.')
# Replace the whole progress sentence, including an inherited malformed range prefix.
old_progress='The roadmap and A0–A4 are authored in the new companion. Continue one section at a time. A3–All foundations are authored; all worked systems and consolidation remain planned; the separate product/analytics track is also later work.'
new_progress='The roadmap, all foundations A0–A4 and S0 are authored in the new companion. Continue one section at a time; remaining worked systems and consolidation remain planned. The separate product/analytics track is also later work.'
replace(roadmap,old_progress,new_progress)
replace('examples/system-design/roadmap/verify.py',
    "'all worked systems and consolidation remain planned' in text",
    "'remaining worked systems and consolidation remain planned' in text")
foundation_group="      { slug: 'foundations', title: 'Foundations', icon: 'Blocks', pages: ['design-method-estimation', 'application-architecture-service-boundaries', 'data-caching-scaling', 'reliable-workflows-concurrency', 'secure-observable-operations'] },"
replace('study-guide/scripts/sync-notes.mjs',foundation_group,
    foundation_group+"\n      { slug: 'worked-systems', title: 'Worked Systems', icon: 'Wrench', pages: ['url-shortener'] },")
replace('Architecture-System-Design-Notes-Plan.md',
    '(roadmap and all foundations A0-A4 available; worked systems/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0 available; S1-S13/consolidation planned)')
replace('Architecture-System-Design-Notes-Plan.md',
    '- [ ] Worked teaching chapters S0-S13 written.',
    '- [x] S0 URL shortener authored with 30 interview Q&As, ten exercises and 118 checks: 16 validation, 24 authority, 16 cache/expiry, twelve analytics, six concurrency, 34 HTTP, two cleanup and eight hypothetical-estimate assertions. Includes unique random-code insert/retry, persistent scoped create replay, four competing worker calls, public GET/HEAD redirects without destination requests, absolute expiry, local disable and bounded lossy analytics.\n- [ ] Remaining worked teaching chapters S1-S13 written.')
replace('Architecture-System-Design-Notes-Plan.md',
    'the roadmap and all foundations A0-A4 are published.',
    'the roadmap, all foundations A0-A4 and S0 are published.')
replace('Architecture-System-Design-Notes-Plan.md',
    'Next: **S0: URL shortener**, then S1-S13 and architecture consolidation.',
    'Next: **S1: Rate limiter**, then S2-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 are authored. Next: **S0: URL shortener**.',
    'All foundations A0-A4 and S0 are authored. Next: **S1: Rate limiter**.')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    ' and [A4](/docs/system-design/secure-observable-operations) available; remaining foundations and worked systems planned separately',
    ', [A4](/docs/system-design/secure-observable-operations) and [S0](/docs/system-design/url-shortener) available; remaining worked systems planned separately')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    'The architecture roadmap and all foundations A0-A4 are available. Next planned section: **S0: URL shortener**;',
    'The architecture roadmap, all foundations A0-A4 and S0 are available. Next planned section: **S1: Rate limiter**;')
replace('examples/system-design/module-4-secure-observable-operations/author.py',
    '**Next: S0 — URL shortener**, architecture part 7 / numeric module 5. The first worked system will combine create/redirect contracts, code uniqueness/collisions, expiry, caching and bounded analytics, then trace failure and scale follow-ups. S0 is planned and has no teaching route yet. All five foundations are authored; worked systems and consolidation continue one section at a time.',
    '**Next: [S0 — URL shortener](/docs/system-design/url-shortener)**, architecture part 7 / numeric module 5. The first worked system combines create/redirect contracts, code uniqueness/collisions, expiry, caching and bounded analytics, with its own local HTTP/SQLite verification scope. All five foundations and S0 are authored; remaining worked systems and consolidation continue one section at a time.')
for script in ('examples/system-design/module-4-secure-observable-operations/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,capture_output=True,
        text=True,encoding='utf-8',check=True)
    print(script+': OK')
files=list((ROOT/'System Design Notes').glob('*.md'))
lines=sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme=ROOT/'README.md'
text=readme.read_text(encoding='utf-8')
text=re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and S0 URL shortener: verified backend/data/cache/workflow/operations probes plus create/redirect uniqueness, retries, expiry, local disable and bounded analytics; S1-S13/consolidation planned |',text)
text=text.replace('the System Design roadmap and all foundations A0-A4 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0 are available;')
text=re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S1, rate limiter.',text)
text=text.replace('architecture companion (roadmap and all foundations available)',
    'architecture companion (roadmap, all foundations and S0 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; first worked system available; next S1')
