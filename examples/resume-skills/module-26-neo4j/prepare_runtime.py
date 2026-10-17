"""Hash-verified portable vendor archives; no installer or Windows service."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request
import zipfile

BASE = Path(__file__).resolve().parent


def prepare(package):
    archives = BASE / '.packages'
    archives.mkdir(exist_ok=True)
    runtime = BASE / '.runtime'
    runtime.mkdir(exist_ok=True)
    archive = archives / package['url'].rsplit('/', 1)[1]
    if not archive.exists():
        partial = archive.with_suffix('.part')
        with urllib.request.urlopen(package['url'], timeout=60) as response, partial.open('wb') as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        partial.replace(archive)
    with archive.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    if digest != package['sha256']:
        raise RuntimeError('Archive checksum mismatch: ' + package['name'])
    with zipfile.ZipFile(archive) as zipped:
        for name in zipped.namelist():
            if not (runtime / name).resolve().is_relative_to(runtime.resolve()):
                raise RuntimeError('Unsafe archive path')
        zipped.extractall(runtime)
    print(package['name'], package['version'], 'verified and extracted', flush=True)


def main():
    packages = json.loads((BASE / 'runtime-packages.json').read_text(encoding='utf-8'))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(prepare, packages))
    (BASE / 'runtime-provenance.json').write_text(json.dumps({
        'packages': packages, 'hashes_verified': True, 'system_install_performed': False,
        'scope': 'Portable vendor distributions; licenses retained in archives and extracted directories.'
    }, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
