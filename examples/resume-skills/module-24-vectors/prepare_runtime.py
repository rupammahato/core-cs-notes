"""Workspace-only portable conda-forge runtime; pinned artifacts recorded before use."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
import re
import tarfile
import urllib.request
import zipfile
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet
import zstandard

BASE = Path(__file__).resolve().parent
RUNTIME = BASE / '.runtime'
LOCK = BASE / 'runtime-packages.json'
PINS = {'postgresql': '16.15', 'libpq': '16.15', 'pgvector': '0.8.6'}


def get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def resolve():
    selected = {}
    constraints = {name: [f'=={version}'] for name, version in PINS.items()}
    pending = list(PINS)
    metadata = {}
    while pending:
        name = pending.pop(0)
        specs = SpecifierSet(','.join(constraints.get(name, [])))
        if name in selected and Version(selected[name]['version']) in specs:
            continue
        if name not in metadata:
            metadata[name] = json.loads(get('https://api.anaconda.org/package/conda-forge/' + name))
        candidates = []
        for entry in metadata[name]['files']:
            try:
                version = Version(entry['version'])
            except InvalidVersion:
                continue
            if entry.get('attrs', {}).get('subdir') in ('win-64', 'noarch') and version in specs and entry.get('sha256'):
                candidates.append(entry)
        if not candidates:
            raise RuntimeError('No compatible package: ' + name + ' ' + str(specs))
        entry = max(candidates, key=lambda f: (Version(f['version']), f['attrs'].get('build_number', 0), f['attrs'].get('timestamp', 0)))
        selected[name] = {'name': name, 'version': entry['version'], 'basename': entry['basename'],
                          'url': 'https:' + entry['download_url'], 'sha256': entry['sha256'],
                          'depends': entry['attrs'].get('depends', [])}
        for dependency in selected[name]['depends']:
            parts = dependency.split()
            depname = parts[0]
            if depname.startswith('__'):
                continue
            spec = parts[1] if len(parts) > 1 else ''
            if spec and spec[0].isdigit():
                spec = '==' + spec
            # These native runtime packages use simple numeric constraints.
            if spec and not re.fullmatch(r'[0-9a-zA-Z.*<>=!,]+', spec):
                raise RuntimeError('Unsupported dependency expression ' + dependency)
            constraints.setdefault(depname, [])
            if spec and spec not in constraints[depname]:
                constraints[depname].append(spec)
            if depname not in pending:
                pending.append(depname)
    return list(selected.values())


def main():
    packages = json.loads(LOCK.read_text(encoding='utf-8')) if LOCK.exists() else resolve()
    LOCK.write_text(json.dumps(packages, indent=2) + '\n', encoding='utf-8')
    RUNTIME.mkdir(exist_ok=True)
    archive_dir = BASE / '.packages'
    archive_dir.mkdir(exist_ok=True)
    def download(package):
        archive = archive_dir / Path(package['basename']).name
        if not archive.exists():
            archive.write_bytes(get('https://conda.anaconda.org/conda-forge/' + package['basename']))
        if hashlib.sha256(archive.read_bytes()).hexdigest() != package['sha256']:
            raise RuntimeError('Package hash mismatch ' + package['name'])
        return archive
    with ThreadPoolExecutor(max_workers=4) as pool:
        archives = list(pool.map(download, packages))
    for package, archive in zip(packages, archives):
        if archive.suffix == '.conda':
            with zipfile.ZipFile(archive) as zipped:
                for name in zipped.namelist():
                    if name.startswith('pkg-') and name.endswith('.tar.zst'):
                        with zstandard.ZstdDecompressor().stream_reader(io.BytesIO(zipped.read(name))) as stream:
                            with tarfile.open(fileobj=stream, mode='r|') as tar:
                                tar.extractall(RUNTIME, filter='data')
        else:
            with tarfile.open(archive, mode='r:bz2') as tar:
                tar.extractall(RUNTIME, filter='data')
        print(package['name'], package['version'], flush=True)
    # Runtime library location belongs to this workspace, not the installed server.
    library = RUNTIME / 'Library'
    control = library / 'share/extension/vector.control'
    control.write_text(control.read_text(encoding='utf-8').replace('$libdir/vector',
                       (library / 'lib/vector').resolve().as_posix()), encoding='utf-8')
    report = {'postgresql': '16.15', 'pgvector': '0.8.6', 'package_count': len(packages),
              'source': 'conda-forge native Windows packages, matching PG16 ABI',
              'sha256_verified': True, 'system_install_performed': False}
    (BASE / 'runtime-provenance.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
