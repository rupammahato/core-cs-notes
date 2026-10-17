import json
from pathlib import Path

class Checks:
    def __init__(self, group):
        self.group = group
        self.rows = []
    def check(self, name, fn):
        fn()
        self.rows.append({'name': name, 'passed': True})
        print('PASS ' + self.group + ': ' + name)
    def save(self, **extra):
        value = {'group': self.group, 'total': len(self.rows), 'checks': self.rows, **extra}
        Path(__file__).with_name(self.group + '-results.json').write_text(
            json.dumps(value, indent=2) + '\n', encoding='utf-8')
        print('PASS ' + self.group + ' total: ' + str(len(self.rows)))
        return value

def equal(actual, expected):
    if actual != expected:
        raise AssertionError((actual, expected))

def require(condition, message='condition failed'):
    if not condition:
        raise AssertionError(message)
