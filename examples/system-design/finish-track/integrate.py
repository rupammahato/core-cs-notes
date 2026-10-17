"""Finish the planned 21-file architecture track without marking learner mastery."""
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
replace(roadmap,"'file':'system-design-handbook-part-21-consolidation.md','status':'Planned'",
    "'file':'system-design-handbook-part-21-consolidation.md','status':'Available' if (ROOT/'System Design Notes/system-design-handbook-part-21-consolidation.md').is_file() else 'Planned'")
replace(roadmap,
    ' and [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag) |',
    ', [S12: Multi-tenant RAG knowledge-base platform](/docs/system-design/multi-tenant-rag), [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline) and [Consolidation and design mocks](/docs/system-design/consolidation) |')
replace(roadmap,'| Planned handbook | 21 files: roadmap, five foundations, fourteen worked designs and consolidation |',
    '| Completed handbook | 21 authored files: roadmap, five foundations, fourteen worked designs and consolidation |')
replace(roadmap,'S0–S12 available; S13 planned','S0–S13 available; all fourteen worked designs authored')
replace(roadmap,
    'This is a syllabus and study guide, not a set of completed worked solutions. Planned chapters are listed without links to nonexistent pages. The site exposes this roadmap, A0–A4 and S0–S12; further chapters appear only when their teaching files exist. Each available chapter has its own implementation, verification scope and learning checklist.',
    'This roadmap links the complete authored track: A0–A4, S0–S13 and final consolidation. All 21 planned files are available on the site. Each teaching chapter has its own implementation, verification scope and unchecked learning checklist; authoring completion does not establish learner mastery or production guarantees.')
replace(roadmap,'It is a practice route; the corresponding worked explanations are still planned.',
    'It is a practice route through authored worked explanations, followed by the final consolidation drills.')
replace(roadmap,
    'These are target routes, not links to future chapters. Use the existing [M28 project explanations](/docs/resume-skills/resume-project-experience-deep-dives) and [M29 revision tools](/docs/resume-skills/consolidation-interview-drills) while the companion is authored.',
    'These are revision routes through authored chapters. Use the existing [M28 project explanations](/docs/resume-skills/resume-project-experience-deep-dives) and [M29 revision tools](/docs/resume-skills/consolidation-interview-drills) alongside the completed architecture companion.')
replace(roadmap,'The refreshed references below are starting points for future chapters.',
    'The references below are the initial reading map for the authored chapters.')
replace(roadmap,'Chapter authors will refresh version-sensitive details at implementation time. Sources here were checked on **16 October 2026**.',
    'Individual chapters record their own reviewed references and runtime evidence. This initial reading map was checked on **16 October 2026**; the authored track was completed on **18 October 2026**.')
replace(roadmap,'| Architecture consolidation | Planned |',
    '| Architecture consolidation | [Available: pattern map, all 60 bank drills, six mocks and final self-test](/docs/system-design/consolidation) |')
replace(roadmap,'## 13. Next','## 13. Continue with revision')
replace(roadmap,
    '**Next: S13 — Analytics event pipeline and dashboard**, architecture part 20 / numeric module 18. It will develop event contracts/identity, event time, duplicate/late data, aggregates and metric definitions.',
    'Finish with [S13: Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline), architecture part 20 / numeric module 18, for event identity, atomic progress, cohorts, late data, rebuild and privacy. Then use [Consolidation and design mocks](/docs/system-design/consolidation), Part 21, for cross-system revision and manual self-assessment.')
replace(roadmap,
    'The roadmap, all foundations A0–A4 and S0–S12 are authored in the new companion. Continue one section at a time; remaining worked systems and consolidation remain planned. The separate product/analytics track is also later work.',
    'The Architecture and System Design track is fully authored: roadmap, all foundations A0–A4, all worked systems S0–S13 and consolidation, 21 files. No planned architecture teaching chapter remains unfinished. Learning checklists remain unchecked for manual self-assessment. The separate product/analytics track P0–P5 remains later work.')
verify = 'examples/system-design/roadmap/verify.py'
replace(verify,
    "'remaining worked systems and consolidation remain planned' in text",
    "'No planned architecture teaching chapter remains unfinished.' in text and len(available)==20 and all(e['status']=='Available' for e in entries)")
replace(verify,"'checked_date':'2026-10-17'","'checked_date':'2026-10-18'")
replace('study-guide/scripts/sync-notes.mjs',
    "'multi-tenant-saas', 'multi-tenant-rag'] },",
    "'multi-tenant-saas', 'multi-tenant-rag', 'analytics-event-pipeline'] },\n      { slug: 'revision', title: 'Revision', icon: 'ListChecks', pages: ['consolidation'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan,'Deliverables at this planning stage:',
    'Deliverables in the completed architecture track:')
replace(plan,'The worked teaching chapters will follow one by one. This plan and the question bank are not completed worked solutions.',
    'All five foundations, fourteen worked systems and final consolidation are now authored in System Design Notes/, alongside the master roadmap: 21 files. This plan and the original question bank remain the syllabus/checkpoint sources; the teaching chapters and final drills supply the worked explanations.')
replace(plan,'(roadmap, all foundations A0-A4 and S0-S12 available; S13/consolidation planned)',
    '(all 21 files authored: roadmap, A0-A4, S0-S13 and consolidation)')
replace(plan,'Sidebar groups will be added only as actual teaching files exist.',
    'All authored chapters are registered under Foundations, Worked Systems and Revision.')
replace(plan,'- [ ] Remaining worked teaching chapter S13 written.',
    '- [x] S13 analytics event pipeline/dashboard authored with 30 interview Q&As, ten tasks and 78 local checks: scoped immutable events, timezone normalization, atomic effects/frontier, exact cohorts, explicit lateness, generation rebuild, subject removal/replay marker, four competing calls, rollback/reopen and real aggregate HTTP. No live Kafka/Beam, connector, browser chart or production load claim.\n'
    '- [x] All fourteen worked systems S0-S13 authored.')
replace(plan,'- [ ] Runnable core mechanisms and verification artifacts created.',
    '- [x] Runnable core mechanisms and verification artifacts created for all 19 teaching chapters; final catalogue preserves 1,600 recorded local assertions with their original runtime/date/scope.')
replace(plan,'- [ ] Timed mock designs and revision sheets completed.',
    '- [x] Final consolidation authored: expanded drills for all 60 bank prompts, fourteen failure cards, 24 confusable pairs, 24 self-tests, six 45-minute mocks, revision routes and a manual-score helper. Learner mastery remains ungraded.')
replace(plan,'the roadmap, all foundations A0-A4 and S0-S12 are published.',
    'all 21 files are published: roadmap, A0-A4, S0-S13 and consolidation.')
replace(plan,'Next: **S13: Analytics event pipeline and dashboard**, then architecture consolidation. The completed Resume Skills handbook supplies the prerequisites.',
    'Authored completion: **all 21 Architecture and System Design files are available**. Continue with consolidation and manual practice; the separate product/analytics track P0-P5 remains later work.')
resume_plan = 'Resume-Skills-Notes-Plan.md'
replace(resume_plan,'All foundations A0-A4 and S0-S12 are authored. Next: **S13: Analytics event pipeline and dashboard**. Continue one section at a time; product/analytics remains later and learning mastery is assessed separately.',
    'The architecture companion is fully authored: all 21 files, including A0-A4, S0-S13 and consolidation. Continue with revision; product/analytics P0-P5 remains a separate later track and learning mastery is assessed separately.')
replace(resume_plan,'- [ ] Worked architecture chapters and implementations written.',
    '- [x] Worked architecture chapters, implementations and final consolidation written; all 21 companion files authored.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,' and [S12](/docs/system-design/multi-tenant-rag) available; remaining worked systems planned separately',
    ', [S12](/docs/system-design/multi-tenant-rag), [S13](/docs/system-design/analytics-event-pipeline) and [architecture consolidation](/docs/system-design/consolidation) available; all 21 architecture files authored')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S12 are available. Next planned section: **S13: Analytics event pipeline and dashboard**; product/analytics remains later.',
    'The architecture roadmap, all foundations A0-A4, all worked systems S0-S13 and consolidation are available: **21 authored architecture files**; product/analytics remains a separate later track.')
replace('examples/system-design/module-17-multi-tenant-rag/lesson.md',
    '**Next: S13 — Analytics event pipeline and dashboard**, architecture part 20 / numeric module 18. It develops event contracts/identity, ingestion, event time, duplicate/late data, aggregates and metric definitions. S13 has no authored teaching route yet. S0–S12 are authored; the final worked system and consolidation remain planned.',
    '**Next: [S13 — Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline)**, architecture part 20 / numeric module 18. It develops scoped event identity, atomic projection progress, cohorts, lateness, rebuild and privacy with local SQLite/HTTP evidence. Finish with [Consolidation and design mocks](/docs/system-design/consolidation), Part 21. All 21 planned architecture files are authored; learner self-assessment remains manual.')
for script in ('examples/system-design/worked-system-s12/author.py','examples/system-design/roadmap/author.py',
               'examples/system-design/roadmap/verify.py','examples/system-design/consolidation/author.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = text.replace('an architecture companion in progress,','a completed 21-part architecture companion,')
text = re.sub(r'\| \*\*System Design(?: \(in progress\))?\*\* \|.*',
    f'| **System Design** | {len(files)} | {lines:,} | Complete roadmap, A0-A4 foundations, S0-S13 worked systems and consolidation; 570 teaching Q&As, all 60 bank drills, six final mocks, scoped runnable examples and recorded verification evidence |',text)
if 'and System Design include dedicated consolidation files.' not in text:
    text = text.replace('include dedicated consolidation files.', 'and System Design include dedicated consolidation files.')
text = text.replace('OOP, OS, DBMS, CN and Resume Skills\nand System Design include',
    'OOP, OS, DBMS, CN, Resume Skills\nand System Design include')
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S12 are available; further architecture and product/analytics chapters remain planned.',
    'the complete System Design track is authored and published. Product/analytics P0-P5 remains a separate later track.')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** All planned architecture chapters are authored; continue with consolidation and manual practice.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S12 available)',
    'completed architecture companion (roadmap, A0-A4, S0-S13 and consolidation)')
readme.write_text(text,encoding='utf-8')
print(f'Completed System Design: {len(files)} files / {lines:,} lines')
