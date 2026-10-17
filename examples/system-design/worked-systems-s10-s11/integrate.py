"""Publish authored S10-S11 together and advance the companion roadmap to S12."""
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
links = '[S10: Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache) and [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas)'
replace(roadmap,
    ' and [S9: Search and autocomplete](/docs/system-design/search-autocomplete) |',
    ', [S9: Search and autocomplete](/docs/system-design/search-autocomplete), '+links+' |')
replace(roadmap,'S0–S9 available; S10–S13 planned','S0–S11 available; S12–S13 planned')
replace(roadmap,'The site exposes this roadmap, A0–A4 and S0–S9;',
    'The site exposes this roadmap, A0–A4 and S0–S11;')
replace(roadmap,
    '**Next: S10 — Load balancer and distributed cache**, architecture part 17 / numeric module 15. It will develop membership/health, placement versus load, hot keys, invalidation and node rejoin.',
    'Continue with '+links+'. They develop placement versus live load, current cache version/rejoin fences, tenant/session/resource authority, invitations, quotas and scoped delayed work. **Next: S12 — Multi-tenant RAG knowledge-base platform**, architecture part 19 / numeric module 17. It will combine versioned ingestion, current scoped retrieval, accepted citations, model/tool budgets, evaluation and deletion.')
replace(roadmap,'The roadmap, all foundations A0–A4 and S0–S9 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S11 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "'checkout-payments-credit-ledger', 'search-autocomplete'] },",
    "'checkout-payments-credit-ledger', 'search-autocomplete', 'load-balancer-distributed-cache', 'multi-tenant-saas'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan,'(roadmap, all foundations A0-A4 and S0-S9 available; S10-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S11 available; S12-S13/consolidation planned)')
replace(plan,'- [ ] Remaining worked teaching chapters S10-S13 written.',
    '- [x] S10 load balancer/distributed cache authored with 30 interview Q&As, ten exercises and 69 local checks: 2,000-key ring/remapping sample, distinct copies, live admission/drain labels, TTL/LRU, canonical version probes, stale-fill/version/epoch/incarnation fences, controlled failure/rejoin, four competing calls, rollback/reopen and real edge HTTP. In-process nodes; no upstream network proxy, Redis replication, automatic detector or throughput claim.\n'
    '- [x] S11 multi-tenant SaaS authored with 30 interview Q&As, ten exercises and 95 local checks: hashed opaque sessions, current role/membership and document/share scope, tenant-switch rotation, removal/logout, last-owner protection, recipient/audience/expiry/revocation-bound invitations, atomic quotas/audit, worker/result rechecks, four competing calls, rollback/reopen and real HTTP. Trusted fixture login; no browser BFF/cookie/CSRF, email, object storage or production RLS integration.\n'
    '- [ ] Remaining worked teaching chapters S12-S13 written.')
replace(plan,'the roadmap, all foundations A0-A4 and S0-S9 are published.',
    'the roadmap, all foundations A0-A4 and S0-S11 are published.')
replace(plan,'Next: **S10: Load balancer and distributed cache**, then S11-S13 and architecture consolidation.',
    'Next: **S12: Multi-tenant RAG knowledge-base platform**, then S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0-S9 are authored. Next: **S10: Load balancer and distributed cache**.',
    'All foundations A0-A4 and S0-S11 are authored. Next: **S12: Multi-tenant RAG knowledge-base platform**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,' and [S9](/docs/system-design/search-autocomplete) available; remaining worked systems planned separately',
    ', [S9](/docs/system-design/search-autocomplete), [S10](/docs/system-design/load-balancer-distributed-cache) and [S11](/docs/system-design/multi-tenant-saas) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S9 are available. Next planned section: **S10: Load balancer and distributed cache**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S11 are available. Next planned section: **S12: Multi-tenant RAG knowledge-base platform**;')
replace('examples/system-design/module-14-search-autocomplete/lesson.md',
    '**Next: S10 — Load balancer and distributed cache**, architecture part 17 / numeric module 15. It develops membership/health, placement versus load, hot keys, invalidation and node rejoin. S10 has no authored teaching route yet. S0–S9 are authored; later systems and consolidation remain planned.',
    '**Next: [S10 — Load balancer and distributed cache](/docs/system-design/load-balancer-distributed-cache)**, architecture part 17 / numeric module 15. It develops placement versus admission, membership/health, TTL/LRU, source version checks, stale-fill fences and cold rejoin with an explicit in-process/edge-HTTP scope. S0–S11 are authored; later systems and consolidation remain planned.')
for script in ('examples/system-design/worked-systems-s7-s9/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S11: links, quotas, delivery, files, booking, chat, feeds, jobs, payment/credit, search, cache placement/rejoin and tenant/session permissions with executable failure checks; S12-S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S9 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S11 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S12, multi-tenant RAG knowledge-base platform.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S9 available)',
    'architecture companion (roadmap, all foundations and S0-S11 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S12')
