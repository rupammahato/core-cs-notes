"""Publish authored S12 and advance all current companion plans to S13."""
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
link = '[S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag)'
replace(roadmap,
    ' and [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas) |',
    ', [S11: Multi-tenant SaaS with authentication and permissions](/docs/system-design/multi-tenant-saas) and '+link+' |')
replace(roadmap,'S0–S11 available; S12–S13 planned','S0–S12 available; S13 planned')
replace(roadmap,'The site exposes this roadmap, A0–A4 and S0–S11;',
    'The site exposes this roadmap, A0–A4 and S0–S12;')
replace(roadmap,
    '**Next: S12 — Multi-tenant RAG knowledge-base platform**, architecture part 19 / numeric module 17. It will combine versioned ingestion, current scoped retrieval, accepted citations, model/tool budgets, evaluation and deletion.',
    'Continue with '+link+' for versioned ingest, current authorized retrieval, request evidence and citation acceptance, bounded uncertain generation and deletion. Its runnable vectors/model are deterministic local fixtures. **Next: S13 — Analytics event pipeline and dashboard**, architecture part 20 / numeric module 18. It will develop event contracts/identity, event time, duplicate/late data, aggregates and metric definitions.')
replace(roadmap,'The roadmap, all foundations A0–A4 and S0–S11 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S12 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "'load-balancer-distributed-cache', 'multi-tenant-saas'] },",
    "'load-balancer-distributed-cache', 'multi-tenant-saas', 'multi-tenant-rag'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan,'(roadmap, all foundations A0-A4 and S0-S11 available; S12-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S12 available; S13/consolidation planned)')
replace(plan,'- [ ] Remaining worked teaching chapters S12-S13 written.',
    '- [x] S12 multi-tenant RAG authored with 30 interview Q&As, ten exercises and 125 local checks: unchanged S11 authority, versioned source/ingest publication, deterministic chunk/vector profiles, current permission/version before top-k, exact request-evidence/citation checks, character-budget reservation/uncertainty, six competing calls, selected judged corpus, deletion/redaction/tombstone, rollback/reopen and real HTTP. Feature-hash vectors and extractive model fixture; no real model/embedding/vector API, tools, stream, object store, provider token/money metering or production quality claim.\n'
    '- [ ] Remaining worked teaching chapter S13 written.')
replace(plan,'the roadmap, all foundations A0-A4 and S0-S11 are published.',
    'the roadmap, all foundations A0-A4 and S0-S12 are published.')
replace(plan,'Next: **S12: Multi-tenant RAG knowledge-base platform**, then S13 and architecture consolidation.',
    'Next: **S13: Analytics event pipeline and dashboard**, then architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0-S11 are authored. Next: **S12: Multi-tenant RAG knowledge-base platform**.',
    'All foundations A0-A4 and S0-S12 are authored. Next: **S13: Analytics event pipeline and dashboard**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,' and [S11](/docs/system-design/multi-tenant-saas) available; remaining worked systems planned separately',
    ', [S11](/docs/system-design/multi-tenant-saas) and [S12](/docs/system-design/multi-tenant-rag) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S11 are available. Next planned section: **S12: Multi-tenant RAG knowledge-base platform**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S12 are available. Next planned section: **S13: Analytics event pipeline and dashboard**;')
replace('examples/system-design/module-16-multi-tenant-saas/lesson.md',
    '**Next: S12 — Multi-tenant RAG knowledge-base platform**, architecture part 19 / numeric module 17. It combines versioned ingestion, current scoped retrieval, accepted citations, model/tool budgets, evaluation and deletion. S12 has no authored teaching route yet. S0–S11 are authored; later systems and consolidation remain planned.',
    '**Next: [S12 — Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag)**, architecture part 19 / numeric module 17. It combines versioned ingest, current authorized retrieval, request evidence/citation acceptance, budget uncertainty and deletion with explicit local vector/model fixtures. S0–S12 are authored; the final worked system and consolidation remain planned.')
for script in ('examples/system-design/worked-systems-s10-s11/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S12: state, failures, cache placement, tenant permissions and versioned RAG evidence/budgets/deletion with executable checks; S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S11 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S12 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S13, analytics event pipeline and dashboard.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S11 available)',
    'architecture companion (roadmap, all foundations and S0-S12 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S13')
