"""Owned temporary embedded engine; native launch, Bolt readiness and clean shutdown."""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from neo4j import GraphDatabase

BASE = Path(__file__).resolve().parent


@contextmanager
def temporary_graph():
    packages = json.loads((BASE / 'runtime-packages.json').read_text(encoding='utf-8'))
    paths = {p['name']: BASE / '.runtime' / p['directory'] for p in packages}
    java = paths['java'] / 'bin/java.exe'
    javac = paths['java'] / 'bin/javac.exe'
    libs = str(paths['neo4j'] / 'lib/*')
    classes = BASE / '.classes'
    classes.mkdir(exist_ok=True)
    build = subprocess.run([str(javac), '-proc:none', '-cp', libs, '-d', str(classes), str(BASE / 'LocalGraphServer.java')],
                           capture_output=True, text=True, encoding='utf-8', timeout=30)
    (BASE / 'java-build-output.txt').write_text(build.stdout + build.stderr, encoding='utf-8')
    build.check_returncode()
    tempbase = Path(tempfile.gettempdir()).resolve()
    target = Path(tempfile.mkdtemp(prefix='placement-m26-', dir=tempbase)).resolve()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    log_path = target / 'console.log'
    log = log_path.open('wb')
    driver = None
    process = None
    evidence = {'port': port, 'loopback_ports_closed': [port], 'system_services_touched': False,
                'authentication': 'disabled only for isolated loopback fixture', 'tls': 'disabled for local Bolt',
                'heap_mib': 256, 'page_cache_mib': 64}
    try:
        process = subprocess.Popen([str(java), '-Xms128m', '-Xmx256m',
            '--add-opens=java.base/java.nio=ALL-UNNAMED', '--add-opens=java.base/java.io=ALL-UNNAMED',
            '-cp', str(classes) + os.pathsep + libs, 'LocalGraphServer', str(target / 'database'), str(port)],
            stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        driver = GraphDatabase.driver(f'bolt://127.0.0.1:{port}', auth=None, connection_timeout=1,
                                     max_connection_pool_size=8, max_transaction_retry_time=2)
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError(log_path.read_text(encoding='utf-8', errors='replace'))
            try:
                driver.verify_connectivity()
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise RuntimeError('Neo4j readiness deadline: ' + log_path.read_text(encoding='utf-8', errors='replace'))
                time.sleep(0.1)
        evidence['java'] = subprocess.run([str(java), '-version'], capture_output=True, text=True, check=True).stderr.splitlines()[0]
        yield driver, evidence
    finally:
        if driver is not None:
            driver.close()
        if process is not None and process.poll() is None:
            process.stdin.write(b'stop\n')
            process.stdin.flush()
            process.stdin.close()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                raise RuntimeError('Owned Neo4j failed clean shutdown')
        log.close()
        evidence['process_exit_code'] = process.returncode if process else None
        evidence['console_log'] = log_path.read_text(encoding='utf-8', errors='replace')
        with socket.socket() as probe:
            probe.settimeout(1)
            evidence['listener_stopped'] = probe.connect_ex(('127.0.0.1', port)) != 0
        if not evidence['listener_stopped']:
            raise RuntimeError('Owned Bolt listener still open')
        if target.parent != tempbase or not target.name.startswith('placement-m26-'):
            raise RuntimeError('Unexpected cleanup path')
        shutil.rmtree(target)
        evidence['temporary_directory_removed'] = not target.exists()
