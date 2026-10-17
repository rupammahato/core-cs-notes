"""Run all examples in fresh interpreters and preserve actual evidence."""
from pathlib import Path
import json
import os
import subprocess
import sys
import sysconfig

if sys.flags.optimize:
    raise SystemExit('Run without -O: these teaching examples use assertions.')
BASE = Path(__file__).resolve().parent
manifest = json.loads((BASE / 'cases.json').read_text(encoding='utf-8'))
env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
results = []
transcript = []
for case in manifest:
    output = subprocess.run([sys.executable, '-X', 'utf8', str(BASE / case['file'])],
                            cwd=BASE, env=env, text=True, encoding='utf-8',
                            capture_output=True, timeout=20)
    actual = output.stdout.replace('\r\n', '\n')
    if output.returncode or output.stderr or actual != case['output']:
        raise AssertionError({'case': case['id'], 'exit': output.returncode,
                              'stdout': actual, 'stderr': output.stderr,
                              'expected': case['output']})
    results.append({'id': case['id'], 'title': case['title'], 'group': case['group'],
                    'file': case['file'], 'passed': True, 'stdout': actual})
    transcript.append('PASS ' + case['id'] + ': ' + case['title'] + '\n' + actual)
domain = subprocess.run([sys.executable, '-X', 'utf8', str(BASE / 'verify_domain.py')],
                        cwd=BASE, env=env, text=True, encoding='utf-8',
                        capture_output=True, timeout=20)
if domain.returncode or domain.stderr:
    raise AssertionError({'domain': domain.stdout, 'stderr': domain.stderr})
domain_data = json.loads(domain.stdout)
for index, case in enumerate(domain_data['checks'], start=1):
    if case['passed'] is not True:
        raise AssertionError(case)
    results.append({'id': 'domain-' + str(index), 'group': 'domain', **case})
    transcript.append('PASS domain-' + str(index) + ': ' + case['name'] + '\n')
counts = {name: sum(row['group'] == name for row in results)
          for name in ('language', 'concurrency', 'domain')}
evidence = {'runtime': {'version': sys.version, 'implementation': sys.implementation.name,
                       'executable': sys.executable,
                       'gil_disabled_build': sysconfig.get_config_var('Py_GIL_DISABLED'),
                       'gil_enabled': sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else None},
            'counts': counts, 'total': len(results), 'results': results,
            'public_response': domain_data['public_response']}
(BASE / 'verification-results.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
transcript.append('PASS total: ' + str(len(results)) + ' (' + ', '.join(str(v) + ' ' + k for k, v in counts.items()) + ')\n')
text = '\n'.join(transcript)
(BASE / 'verification-output.txt').write_text(text, encoding='utf-8')
print(text, end='')
