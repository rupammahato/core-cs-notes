"""Read user PDFs into a project-only evidence catalogue; omit contact/education data."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import re
from pypdf import PdfReader

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
projects = [
    ('neosophical', 'Neosophical Labs'), ('datsol', 'Datsol Solutions'),
    ('10x', '10X Analysts'), ('zyke', 'Zyke'),
    ('load-balancer', 'Consistent Hashing Load Balancer'),
    ('megalith', 'Megalith'), ('membition', 'Membition'),
]
sources = []
for filename in ('Rupam_Resume_Updated.pdf', 'Rupam_Resume_Product.pdf'):
    path = ROOT / filename
    pages = [page.extract_text() for page in PdfReader(path).pages]
    text = '\n'.join(pages)
    selected = text[text.index('Experience'):text.index('Positions of Responsibility')]
    found = []
    for identity, anchor in projects:
        match = re.search(r'^' + re.escape(anchor), selected, re.M)
        assert match, (filename, identity)
        found.append((match.start(), identity, anchor))
    found.sort()
    excerpts = []
    for index, (start, identity, anchor) in enumerate(found):
        end = found[index + 1][0] if index + 1 < len(found) else len(selected)
        snippet = selected[start:end].replace('Entrepreneurial Experience', '').replace('Key Projects', '').strip()
        excerpts.append({'project_id': identity, 'anchor': anchor, 'page': next(i for i, p in enumerate(pages, 1) if snippet.splitlines()[0] in p), 'text': snippet, 'evidence_class': 'resume-reported', 'original_code_or_metrics_reproduced': False})
    sources.append({'file': filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'excerpts': excerpts})
catalogue = {'checked_date': '2026-10-16', 'pypdf': importlib.metadata.version('pypdf'), 'sources': sources, 'scope': 'User-provided resume text, not independent proof of production behavior, ownership, revenue or benchmark results. Contacts and education omitted.'}
(BASE / 'resume-evidence.json').write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'sources': len(sources), 'projects_per_source': [len(s['excerpts']) for s in sources], 'pypdf': catalogue['pypdf']}, indent=2))
