"""Fetch exact retained physical sources; never accept a rerun or replaced zip."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[2]


def api(path):
    return json.loads(subprocess.check_output(['gh','api',path]))


def admit_run(actual, expected):
    if actual.get('status')!='completed' or any(actual.get(k)!=v for k,v in expected.items()):
        raise ValueError('Physical source producer changed')


def extract(archive, destination):
    with zipfile.ZipFile(archive) as bundle:
        names=bundle.namelist()
        if len(names)!=len(set(names)) or any(Path(n).is_absolute() or '..' in Path(n).parts
                or '\\' in n for n in names):
            raise ValueError('Unsafe or duplicate source archive member')
        if any((i.external_attr>>16)&0o170000==0o120000 for i in bundle.infolist()):
            raise ValueError('Source archive contains a symlink')
        bundle.extractall(destination)


def artifact(repo,expected,out):
    actual=api(f'repos/{repo}/actions/artifacts/{expected["id"]}')
    if (actual.get('expired') is not False or actual.get('workflow_run',{}).get('id')!=expected['source_run']
            or any(actual.get(k)!=expected[k] for k in ('id','name','digest','size_in_bytes'))):
        raise ValueError('Physical source archive identity changed')
    archive=out/(expected['name']+'.zip')
    with archive.open('wb') as stream:
        subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{expected["id"]}/zip'],stdout=stream,check=True)
    if (archive.stat().st_size!=expected['size_in_bytes'] or
            'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest()!=expected['digest']):
        raise ValueError('Downloaded physical source archive changed')
    destination=out/expected['name'];extract(archive,destination)
    (out/(expected['name']+'.metadata.json')).write_text(json.dumps(actual,indent=2)+'\n')
    return destination


def fetch(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    repo=os.environ['GITHUB_REPOSITORY'];manifest=json.loads((ROOT/'spikes/r1/assembly_sources.json').read_text())
    for run,expected in manifest['producers'].items():
        actual=api(f'repos/{repo}/actions/runs/{run}');admit_run(actual,expected)
        (out/(run+'.producer.json')).write_text(json.dumps(actual,indent=2)+'\n')
    roots={}
    def leaf(item):
        case,expected=item;path=artifact(repo,expected,out)
        return case,str(path/'leaf_finish')
    with ThreadPoolExecutor(max_workers=4) as pool:
        for case,path in pool.map(leaf,manifest['contexts'].items()):
            roots[case]=path
    (out/'sources.json').write_text(json.dumps(roots,indent=2)+'\n')
    # Frozen failed original is the authenticated graph/model control.
    from unused_lut_probe import context,SOURCE_RUN,ARTIFACT_ID,ARCHIVE_SHA
    run=api(f'repos/{repo}/actions/runs/{SOURCE_RUN}')
    meta=api(f'repos/{repo}/actions/artifacts/{ARTIFACT_ID}');context(run,meta)
    capsule=artifact(repo,dict(id=ARTIFACT_ID,name=meta['name'],digest='sha256:'+ARCHIVE_SHA,
                              size_in_bytes=meta['size_in_bytes'],source_run=SOURCE_RUN),out)
    (out/'original-source.json').write_text(json.dumps(dict(run=run,artifact=meta),indent=2)+'\n')
    native_run=44461373512
    expected=dict(id=native_run,head_sha='afc68e55411a4f582928e3dae2d11e46a22d5141',
                  head_branch='efpga',run_attempt=1,conclusion='success',
                  path='.github/workflows/r1_registered_input_functional.yaml')
    actual=api(f'repos/{repo}/actions/runs/{native_run}');admit_run(actual,expected)
    native=artifact(repo,dict(id=14499804479,name='r1-registered-input-native-44461373512',
        digest='sha256:cb142dcbf5856f400439472150bdb6dce04b97cb034647af88f7eb8b5dc7e4f2',
        size_in_bytes=8969665,source_run=native_run),out)
    (out/'locations.json').write_text(json.dumps(dict(capsule=str(capsule),sources=str(out/'sources.json'),
        native=str(native/'registered_native/all-native.json')),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    fetch(**vars(p.parse_args()))
