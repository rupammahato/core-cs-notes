"""Optional manual lesson with temporary data and a best-effort analytics batch thread."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event,Thread
from time import time

from shortener import Store
from service import Service
from http_api import make_server


def main():
    with TemporaryDirectory(prefix='placement-s0-manual-') as directory:
        store = Store(Path(directory)/'shortener.sqlite')
        service = Service(store,time)
        server = make_server(service)
        stop = Event()

        def aggregate():
            while not stop.wait(0.5):
                service.flush_analytics()

        worker = Thread(target=aggregate)
        worker.start()
        print(f'Lesson API: http://127.0.0.1:{server.server_port}',flush=True)
        print('Management credential: Authorization: Bearer lesson-alice',flush=True)
        print('Use the printed local origin for /r/CODE; short.example is illustrative.',flush=True)
        print('Ctrl+C closes the API/worker and removes this session database.',flush=True)
        try:
            server.serve_forever(poll_interval=0.05)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
            stop.set()
            worker.join()
            store.close()


if __name__=='__main__':
    main()
