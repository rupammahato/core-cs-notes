"""Publish the three requested sections together and advance the roadmap to S7."""
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
replace(roadmap,
    ' and [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing) |',
    ', [S3: File upload, storage and processing service](/docs/system-design/file-upload-processing), [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging) and [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing) |')
replace(roadmap,'S0–S3 available; S4–S13 planned','S0–S6 available; S7–S13 planned')
replace(roadmap,'The site exposes this roadmap, A0–A4 and S0–S3;',
    'The site exposes this roadmap, A0–A4 and S0–S6;')
replace(roadmap,
    '**Next: S4 — Ticket booking and limited-inventory reservation**, architecture part 11 / numeric module 9. It will develop authoritative inventory, atomic holds, expiry, concurrent booking attempts and late-payment decisions.',
    'Continue with [S4: Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations), [S5: Chat and real-time messaging](/docs/system-design/chat-messaging) and [S6: Social feed and photo sharing](/docs/system-design/social-feed-photo-sharing). They develop inventory/payment boundaries, durable reconnectable messaging and privacy-aware hybrid feeds. **Next: S7 — Background job scheduler and worker platform**, architecture part 14 / numeric module 12. It will generalize job identity, scheduling, claims/leases, retries, fairness and backlog recovery.')
replace(roadmap,'The roadmap, all foundations A0–A4 and S0–S3 are authored in the new companion.',
    'The roadmap, all foundations A0–A4 and S0–S6 are authored in the new companion.')
replace('study-guide/scripts/sync-notes.mjs',
    "pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks', 'file-upload-processing'] },",
    "pages: ['url-shortener', 'rate-limiter', 'notifications-webhooks', 'file-upload-processing', 'booking-reservations', 'chat-messaging', 'social-feed-photo-sharing'] },")
plan = 'Architecture-System-Design-Notes-Plan.md'
replace(plan,'(roadmap, all foundations A0-A4 and S0-S3 available; S4-S13/consolidation planned)',
    '(roadmap, all foundations A0-A4 and S0-S6 available; S7-S13/consolidation planned)')
replace(plan,'- [ ] Remaining worked teaching chapters S4-S13 written.',
    '- [x] S4 ticket booking/reservations authored with 30 interview Q&As, ten exercises and 57 local checks: atomic group holds, expiry/replay, two last-seat contenders, signed callback binding, payment/event dedupe, late-charge compensation intent and rollback. No real payment/refund is executed.\n'
    '- [x] S5 chat/messaging authored with 30 interview Q&As, ten exercises and 59 local checks: durable send/ack replay, room sequence, high-water catchup, bounded lossy hints, membership revocation, monotonic reported reads, restart and four competing calls. Actual transport is HTTP polling; WebSocket is discussed, not implemented.\n'
    '- [x] S6 social feed/photo sharing authored with 30 interview Q&As, ten exercises and 67 local checks: ready-media/version ownership, durable batched push rollback/frontier, pull merge, follow backfill, current graph/block/delete filtering, scoped keyset cursors and four competing calls. Media is a metadata fixture, not an image/S3 integration.\n'
    '- [ ] Remaining worked teaching chapters S7-S13 written.')
replace(plan,'the roadmap, all foundations A0-A4 and S0-S3 are published.',
    'the roadmap, all foundations A0-A4 and S0-S6 are published.')
replace(plan,'Next: **S4: Ticket booking and limited-inventory reservation**, then S5-S13 and architecture consolidation.',
    'Next: **S7: Background job scheduler and worker platform**, then S8-S13 and architecture consolidation.')
replace('Resume-Skills-Notes-Plan.md',
    'All foundations A0-A4 and S0-S3 are authored. Next: **S4: Ticket booking and limited-inventory reservation**.',
    'All foundations A0-A4 and S0-S6 are authored. Next: **S7: Background job scheduler and worker platform**.')
resume = 'Resume Skills Notes/resume-skills-handbook-part-1-master-roadmap.md'
replace(resume,' and [S3](/docs/system-design/file-upload-processing) available; remaining worked systems planned separately',
    ', [S3](/docs/system-design/file-upload-processing), [S4](/docs/system-design/booking-reservations), [S5](/docs/system-design/chat-messaging) and [S6](/docs/system-design/social-feed-photo-sharing) available; remaining worked systems planned separately')
replace(resume,
    'The architecture roadmap, all foundations A0-A4 and S0-S3 are available. Next planned section: **S4: Ticket booking and limited-inventory reservation**;',
    'The architecture roadmap, all foundations A0-A4 and S0-S6 are available. Next planned section: **S7: Background job scheduler and worker platform**;')
replace('examples/system-design/module-8-file-upload-processing/author.py',
    '**Next: S4 — Ticket booking and limited-inventory reservation**, architecture part 11 / numeric module 9. It will develop authoritative inventory, atomic holds, expiry, concurrent booking attempts and late-payment decisions. S4 is planned and has no teaching route yet. Continue one section at a time; remaining worked systems and architecture consolidation remain planned.',
    '**Next: [S4 — Ticket booking and limited-inventory reservation](/docs/system-design/booking-reservations)**, architecture part 11 / numeric module 9. It develops authoritative inventory, atomic holds, expiry, concurrent booking attempts and late-payment decisions with its own local SQLite/signed-HTTP scope. S4-S6 are also authored; remaining systems and architecture consolidation remain planned.')
for script in ('examples/system-design/module-8-file-upload-processing/author.py',
               'examples/system-design/roadmap/author.py','examples/system-design/roadmap/verify.py'):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/script)],cwd=ROOT,
        capture_output=True,text=True,encoding='utf-8',check=True)
    print(script+': OK')
files = list((ROOT/'System Design Notes').glob('*.md'))
lines = sum(file.read_text(encoding='utf-8').count('\n') for file in files)
readme = ROOT/'README.md'
text = readme.read_text(encoding='utf-8')
text = re.sub(r'\| \*\*System Design \(in progress\)\*\* \|.*',
    f'| **System Design (in progress)** | {len(files)} | {lines:,} | Roadmap, foundations A0-A4 and worked systems S0-S6: links, quotas, delivery, file lifecycle, atomic booking, reconnectable chat and hybrid private feeds with executable failure checks; S7-S13/consolidation planned |',text)
text = text.replace('the System Design roadmap, all foundations A0-A4 and S0-S3 are available;',
    'the System Design roadmap, all foundations A0-A4 and S0-S6 are available;')
text = re.sub(r'\*\*System Design: \d+ files, [\d,]+ lines\.\*\* Next:.*',
    f'**System Design: {len(files)} files, {lines:,} lines.** Next: S7, background job scheduler and worker platform.',text)
text = text.replace('architecture companion (roadmap, all foundations and S0-S3 available)',
    'architecture companion (roadmap, all foundations and S0-S6 available)')
readme.write_text(text,encoding='utf-8')
print(f'System Design: {len(files)} files / {lines:,} lines; next S7')
