"""Source-bundle integrity and local promotion helpers, not a deployment platform."""
from pathlib import Path
import hashlib,json,os,zipfile

FILES=('app.mjs','telemetry.mjs','serve.mjs','load.mjs','statistics.mjs','contract.test.mjs','package.json','package-lock.json')
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def package(source,destination,revision,release):
    source,destination=Path(source),Path(destination)
    manifest={'revision':revision,'release':release,'files':{name:digest(source/name) for name in FILES}}
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:archive.write(source/name,name)
        archive.writestr('manifest.json',json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest,digest(destination)

def extract_verified(archive_path,expected_digest,destination):
    destination=Path(destination).resolve()
    if digest(archive_path)!=expected_digest:raise ValueError('Artifact digest mismatch')
    with zipfile.ZipFile(archive_path) as archive:
        names=archive.namelist()
        if len(names)!=len(FILES)+1 or set(names)!=set(FILES)|{'manifest.json'}:
            raise ValueError('Unexpected archive paths')
        destination.mkdir()
        for name in names:
            if (destination/name).resolve().parent!=destination:raise ValueError('Archive path escaped release')
        archive.extractall(destination)
    manifest=json.loads((destination/'manifest.json').read_text())
    if set(manifest['files'])!=set(FILES) or not all(digest(destination/name)==value for name,value in manifest['files'].items()):
        raise ValueError('Extracted source mismatch')
    return manifest

def promote(pointer,manifest,artifact_digest):
    pointer=Path(pointer)
    temporary=pointer.with_name('current.new.json')
    temporary.write_text(json.dumps({'release':manifest['release'],'revision':manifest['revision'],'artifact_sha256':artifact_digest},indent=2)+'\n')
    os.replace(temporary,pointer)
