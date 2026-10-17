"""Update A1 progress and navigation without touching the original core handbooks."""
from pathlib import Path
import re
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]

def replace(path, old, new):
    source = ROOT/path
    text = source.read_text(encoding='utf-8')
    if new in text:
        pass
    elif old in text:
        text = text.replace(old, new)
    else:
        raise AssertionError((path, old))
    source.write_text(text, encoding='utf-8')

roadmap = 'examples/system-design/roadmap/author.py'
replace(roadmap,
    'This master roadmap and [A0: How to approach a design question](/docs/system-design/design-method-estimation) |',
    'This master roadmap, [A0: How to approach a design question](/docs/system-design/design-method-estimation) and [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries) |')
replace(roadmap, 'A0 available; A1–A4 planned', 'A0 and A1 available; A2–A4 planned')
replace(roadmap, 'The site exposes this roadmap and A0;', 'The site exposes this roadmap, A0 and A1;')
replace(roadmap,
    'Start with [A0: How to approach a design question](/docs/system-design/design-method-estimation). **Next: A1 — Application architecture and service boundaries**, architecture part 3 / numeric module 1. It will develop application responsibilities and a concrete request trace.',
    'Start with [A0: How to approach a design question](/docs/system-design/design-method-estimation), then [A1: Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries). **Next: A2 — Data, caching and scaling**, architecture part 4 / numeric module 2. It will connect access patterns and consistency requirements to data and scaling choices.')
replace(roadmap, 'The roadmap and A0 are authored in the new companion.', 'The roadmap, A0 and A1 are authored in the new companion.')
replace(roadmap, 'A1–A4, all worked systems and consolidation remain planned', 'A2–A4, all worked systems and consolidation remain planned')

replace('study-guide/scripts/sync-notes.mjs', "pages: ['design-method-estimation']", "pages: ['design-method-estimation', 'application-architecture-service-boundaries']")
replace('Architecture-System-Design-Notes-Plan.md', '(roadmap and A0 available; later chapters planned)', '(roadmap, A0 and A1 available; later chapters planned)')
replace('Architecture-System-Design-Notes-Plan.md',
    '- [ ] Foundation and worked teaching chapters written.',
    '- [x] A1 authored with 30 interview Q&As, ten exercises and 67 checks: four runtime-import boundary, 17 direct service/repository, four transaction and 42 real HTTP assertions. Includes a TypeScript/Express backend, observed request trace, ownership and deployment decisions, fixed public lesson-token scope and temporary-data/listener cleanup.\n- [ ] Foundation and worked teaching chapters written.')
replace('Architecture-System-Design-Notes-Plan.md', 'the roadmap and A0 are published.', 'the roadmap, A0 and A1 are published.')
replace('Architecture-System-Design-Notes-Plan.md',
    'Next: **A1: Application architecture and service boundaries**, then A2-A4 and the worked designs beginning with S0.',
    'Next: **A2: Data, caching and scaling**, then A3-A4 and the worked designs beginning with S0.')
replace('Resume-Skills-Notes-Plan.md',
    'Next: **A1: Application architecture and service boundaries**.',
    'A0 and A1 are authored. Next: **A2: Data, caching and scaling**.')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    '[Master roadmap](/docs/system-design) and [A0](/docs/system-design/design-method-estimation) available;',
    '[Master roadmap](/docs/system-design), [A0](/docs/system-design/design-method-estimation) and [A1](/docs/system-design/application-architecture-service-boundaries) available;')
replace('Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md',
    'Next planned extension: **the architecture companion roadmap, then A0: How to approach a design question**;',
    'The architecture roadmap, A0 and A1 are available. Next planned section: **A2: Data, caching and scaling**;')

# Keep the predecessor's generator and teaching source consistent.
replace('examples/system-design/module-0-design-method/author.py',
    'A1 will develop application responsibilities and a framework baseline.',
    '[A1](/docs/system-design/application-architecture-service-boundaries) develops application responsibilities and a framework baseline.')
replace('examples/system-design/module-0-design-method/author.py',
    'A1 will supply application responsibilities and a framework baseline;',
    '[A1](/docs/system-design/application-architecture-service-boundaries) supplies application responsibilities and a framework baseline;')
replace('examples/system-design/module-0-design-method/author.py',
    '**Next: A1 — Application architecture and service boundaries.**',
    '**Next: [A1 — Application architecture and service boundaries](/docs/system-design/application-architecture-service-boundaries).**')
for script in ('examples/system-design/module-0-design-method/author.py', 'examples/system-design/roadmap/author.py', 'examples/system-design/roadmap/verify.py'):
    result = subprocess.run([sys.executable, '-X', 'utf8', str(ROOT/script)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    print(script + ': OK')

readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, A0 design method and A1 application architecture: estimates, state ownership, controller/service/repository boundaries, a verified TypeScript/Express + SQLite backend, request traces and service/gateway/event trade-offs; remaining foundations/worked systems planned |', text)
text = text.replace('the System Design roadmap and A0 are available;', 'the System Design roadmap, A0 and A1 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: A2, data, caching and scaling.', text)
text = text.replace('architecture companion (roadmap and A0 available)', 'architecture companion (roadmap, A0 and A1 available)')
readme.write_text(text, encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next A2')
