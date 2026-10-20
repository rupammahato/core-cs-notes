"""Consolidate completed checks without rerunning unrelated prior subject suites."""
import hashlib
import json
import socket
import subprocess
from fixtures import BASE

ROOT = BASE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def listening(port):
    with socket.socket() as client:
        client.settimeout(1)
        return client.connect_ex(('127.0.0.1', port)) == 0


def main():
    def read(name):
        return json.loads((BASE / name).read_text(encoding='utf-8'))
    runtime, content, site = [read(name) for name in ['verification-results.json', 'content-validation.json', 'site-validation.json']]
    assert runtime['total'] == 57 and all(check['passed'] for check in runtime['checks'])
    assert content['total'] == 58 and all(check['passed'] for check in content['checks'])
    assert all(sha(BASE / name) == value for name, value in runtime['source_sha256'].items())
    assert all(sha(ROOT / name) == value for name, value in content['source_sha256'].items())
    prior = read('prior-notes-snapshot.json')
    assert len(prior) == 163 and all(sha(ROOT / name) == value for name, value in prior.items())
    assert len(site['routes']) == 175 and all(row['status'] == 200 for row in site['routes'])
    assert len(site['assertions']) == 23 and all(site['assertions'].values())
    assert len(site['search']) == 17 and all(row['indexed'] and row['scoped'] for row in site['search'].values())
    assert site['missingChapterStatus'] == 404 and site['temporaryServerClosed']
    assert site['port'] != 3000 and not listening(site['port'])
    assert not listening(3000), 'Port 3000 is unexpectedly listening; inspect ownership before stopping anything.'
    build_log = (BASE / 'site-build-output.txt').read_text(encoding='utf-8-sig')
    assert 'Compiled successfully' in build_log and '179/179' in build_log and 'Finished TypeScript' in build_log
    whitespace = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert whitespace.returncode == 0, whitespace.stdout + whitespace.stderr
    own_files = [p for p in BASE.iterdir() if p.is_file() and p.suffix in ['.py', '.mjs', '.hpp', '.cpp', '.md', '.json']]
    own_files += [BASE / '.gitignore']
    for path in own_files:
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            assert line == line.rstrip(), f'Trailing whitespace in {path.name}'
    summary = {
        'verified_date': '2026-10-21', 'status': 'passed',
        'book': {key: content[key] for key in ['chapters', 'lines', 'implementations', 'worked_traces', 'interview_answers', 'practice_tasks', 'oral_checks', 'mocks']},
        'runtime': {'groups': runtime['total'], 'commands_checked': runtime['commands_checked'],
                    'direct_api_assertions': runtime['direct_api_assertions'], 'compiler': runtime['compiler'], 'flags': runtime['flags']},
        'content': {'audit_groups': content['total'], 'protected_prior_notes_unchanged': 163},
        'website': {'production_build': 'passed; exec exit code 0 observed', 'static_pages_generated': 179,
                    'page_routes_200': len(site['routes']), 'content_assertions': len(site['assertions']),
                    'scoped_search_queries': len(site['search']), 'missing_chapter_status': 404,
                    'temporary_preview_port': site['port'], 'temporary_preview_closed': True, 'port_3000_listening': False,
                    'font_fixture': 'Existing local Google-font response fixture used through NEXT_FONT_GOOGLE_MOCKED_RESPONSES; normal site font configuration unchanged.',
                    'visual_browser_review': False},
        'git_diff_whitespace_check': 'passed', 'scope_boundaries': runtime['boundaries'],
        'evidence_sha256': {name: sha(BASE / name) for name in ['verification-results.json', 'observations.json',
            'compile-output.json', 'content-validation.json', 'site-validation.json', 'site-build-output.txt', 'research.json']},
        'tool_source_sha256': {path.name: sha(path) for path in own_files if path.suffix in ['.py', '.mjs', '.hpp', '.cpp']},
    }
    (BASE / 'validation-summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'chapters': content['chapters'],
                      'routes_checked': len(site['routes']), 'prior_notes_unchanged': 163, 'server_stopped': True}))


if __name__ == '__main__':
    main()
