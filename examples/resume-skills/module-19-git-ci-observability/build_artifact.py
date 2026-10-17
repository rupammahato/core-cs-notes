"""Build the teaching source bundle; does not upload, publish or deploy."""
from pathlib import Path
import argparse,json
from release import package
parser=argparse.ArgumentParser()
parser.add_argument('--revision',required=True)
args=parser.parse_args()
if len(args.revision)!=40 or any(c not in '0123456789abcdef' for c in args.revision):
    raise SystemExit('Expected a full SHA-1 source revision for this fixture')
base=Path(__file__).resolve().parent
manifest,sha=package(base,base/'release-artifact.zip',args.revision,'candidate')
(base/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
(base/'release-artifact.sha256').write_text(sha+'  release-artifact.zip\n',encoding='utf-8')
print(json.dumps({'revision':args.revision,'artifact_sha256':sha}))
