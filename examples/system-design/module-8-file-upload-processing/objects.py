"""Private local immutable objects. Trusted root; no user-supplied disk paths."""
from pathlib import Path
import os
import re
import uuid


class Objects:
    def __init__(self, root):
        self.root = Path(root).resolve()
        for area in ('raw', 'derived'):
            (self.root/area).mkdir(parents=True, exist_ok=True)

    def path(self, area, key):
        pattern = r'[a-f0-9]{32}' if area == 'raw' else r'[a-f0-9]{32}\.[a-f0-9]{32}'
        if area not in ('raw', 'derived') or not re.fullmatch(pattern, key):
            raise ValueError('invalid server object key')
        target = (self.root/area/key).resolve()
        if target.parent != (self.root/area).resolve():
            raise ValueError('object escaped owned area')
        return target

    def put(self, area, key, data):
        target = self.path(area, key)
        staging = target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
        try:
            with staging.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # Install complete bytes without replacing an existing version.
                os.link(staging, target)
                return True
            except FileExistsError:
                if target.read_bytes() != data:
                    raise ValueError('immutable object conflict')
                return False
        finally:
            staging.unlink(missing_ok=True)

    def read(self, area, key):
        # Fixture size is bounded at ingress; detect unexpected oversized disk state.
        with self.path(area, key).open('rb') as stream:
            data = stream.read(4097)
        if len(data) > 4096:
            raise ValueError('unexpected oversized stored object')
        return data

    def inventory(self):
        return [(area, file) for area in ('raw', 'derived')
                for file in (self.root/area).iterdir() if file.is_file()]

    def remove_owned(self, area, file):
        target = file.resolve()
        if area not in ('raw', 'derived') or target.parent != (self.root/area).resolve():
            raise ValueError('cleanup escaped owned area')
        target.unlink(missing_ok=True)
