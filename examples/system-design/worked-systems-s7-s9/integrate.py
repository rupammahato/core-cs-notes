"""Integrate authored S7-S9 and advance availability and plans to S10."""
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]


def replace(path,old,new):
    file = ROOT/path
    text = file.read_text(encoding='utf-8')
    if new in text:
        return
    assert old in text,(path,old)
    file.write_text(text.replace(old,new),encoding='utf-8')


roadmap = 'examples/system-design/roadmap/author.py'
new_links = '[S7: Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers), [S8: Checkout, payments and credit ledger](/docs/system-design/checkout-payments-credit-ledger) and [S9: Search and autocomplete](/docs/system-design/search-autocomplete)'
replace(roadmap,
    ' and [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing) |',
    ', [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing), '+new_links+' |')
replace(roadmap,'S0–S6 available; S7–S13 planned','S0–S9 available; S10–S13 planned')
replace(roadmap,'The site exposes this roadmap, A0–A4 and S0–S6;',
    'The site exposes this roadmap, A0–A4 and S0–S9;')
replace(roadmap,
    '**Next: S7 — Background job scheduler and worker platform**, architecture part 14 / numeric module 12. It will generalize job identity, scheduling, claims/leases, retries, fairness and backlog recovery.',
    'Continue with '+new_links+'. They develop recoverable job effects, uncertain payment commits, balanced credit posting and current-authorized search over asynchronous projections. **Next: S10 — Load balancer and distributed cache**, architecture part 17 / numeric module 15. It will develop membership/health, placement versus load, hot keys, invalidation and node rejoin.')
replace(roadmap,'The roadmap, all foundations A0–A4 and S0–S6 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S9 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "'booking-reservations', 'chat-messaging', 'social-feed-photo-sharing'] },",
    "'booking-reservations', 'chat-messaging', 'social-feed-photo-sharing', 'job-scheduler-workers', 'checkout-payments-credit-ledger', 'search-autocomplete'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan,'(roadmap, all foundations A0-A4 and S0-S6 available; S7-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S9 available; S10-S13/consolidation planned)')
replace(plan,'- [ ] Remaining worked teaching chapters S7-S13 written.',
    '- [x] S7 job scheduler/workers authored with 30 interview Q&As, ten exercises and 65 local checks: durable occurrence/frontier, original-intent replay, two concurrent claims, tenant admission, fenced leases, bounded renewal/retries, local effect-before-ack recovery, rollback and real HTTP. Explicit fixture time; no broker, cron daemon or remote effect.\n'
    '- [x] S8 checkout/payments/credit ledger authored with 30 interview Q&As, ten exercises and 62 local checks: separate provider commit and reply-loss injection, catalog snapshot, event/payment/grant dedupe, signed fixture callback, four competing calls, balanced CREDIT journals, nonnegative spends, reversal, rollback and HTTP. No real charge, cash ledger or external refund.\n'
    '- [x] S9 search/autocomplete authored with 30 interview Q&As, ten exercises and 77 local checks: actual SQLite FTS5, title-token prefixes, source/outbox atomicity, stale/tombstone fences, current tenant/ACL/version before top-k, two competing projectors, local rebuild, rollback and HTTP. No external cluster, semantic model, online reindex or throughput claim.\n'
    '- [ ] Remaining worked teaching chapters S10-S13 written.')
replace(plan,'the roadmap, all foundations A0-A4 and S0-S6 are published.',
    'the roadmap, all foundations A0-A4 and S0-S9 are published.')
replace(plan,'Next: **S7: Background job scheduler and worker platform**, then S8-S13 and architecture consolidation.',
    'Next: **S10: Load balancer and distributed cache**, then S11-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0-S6 are authored. Next: **S7: Background job scheduler and worker platform**.',
    'All foundations A0-A4 and S0-S9 are authored. Next: **S10: Load balancer and distributed cache**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,' and [S6](/docs/system-design/social-feed-photo-sharing) available; remaining worked systems planned separately',
    ', [S6](/docs/system-design/social-feed-photo-sharing), [S7](/docs/system-design/job-scheduler-workers), [S8](/docs/system-design/checkout-payments-credit-ledger) and [S9](/docs/system-design/search-autocomplete) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S6 are available. Next planned section: **S7: Background job scheduler and worker platform**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S9 are available. Next planned section: **S10: Load balancer and distributed cache**;')
replace('examples/system-design/module-11-social-feed-photo-sharing/lesson.md',
    '**Next: S7 — Background job scheduler and worker platform**, architecture part 14 / numeric module 12. It will generalize job identity, scheduling, leases, retries, fairness and backlog recovery. S7 has no authored teaching route yet. S0–S6 are authored; later worked systems and consolidation remain planned.',
    '**Next: [S7 — Background job scheduler and worker platform](/docs/system-design/job-scheduler-workers)**, architecture part 14 / numeric module 12. It develops durable occurrence/frontier, fenced leases, tenant admission, bounded retries and local effect-before-ack recovery with its own SQLite/HTTP scope. S0–S9 are authored; later worked systems and consolidation remain planned.')
for script in ('examples/system-design/worked-systems-s4-s6/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S9: links, quotas, delivery, files, booking, chat, feeds, recoverable jobs, payment/credit boundaries and private search with executable failure checks; S10-S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S6 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S9 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S10, load balancer and distributed cache.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S6 available)',
    'architecture companion (roadmap, all foundations and S0-S9 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S10')
