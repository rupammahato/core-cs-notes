"""Optional manual loopback demo; no persistent service or port 3000."""
from tempfile import TemporaryDirectory
from pathlib import Path
from http_api import Context, server
from limiter import Store

with TemporaryDirectory(prefix='placement-s1-manual-') as directory:
    path = Path(directory) / 'quota.sqlite'
    initial = Store(path)
    initial.close()
    api = server(Context(path))
    print(f'Lesson API: http://127.0.0.1:{api.server_port}', flush=True)
    print('Bearer lesson-alice; GET /api/read or empty POST /api/write. Ctrl+C stops.', flush=True)
    try:
        api.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        api.server_close()
