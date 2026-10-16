"""Portable native artifact audit without EDA, network, or worktree specs."""
import json
from pathlib import Path

import pytest
import yaml

from autonomy import architecture_evidence as a
from autonomy import supervisor

REV = 'a'*40
RUN = '123456'


def dump(path, value):
    path.write_text(json.dumps(value))


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    sources = {}
    for design in a.hosted.DESIGNS:
        sources['protocols/'+design+'/pins.yaml'] = yaml.safe_dump({'top': design+'_top', 'params': {'PRIMS': 1, 'RATE': 4}}).encode()
        sources['protocols/'+design+'/user.v'] = b'module fixture; endmodule\n'
    for name in ['tools/compile/compile.py', 'tools/compile/bitfile.py', 'tools/compile/bitgen.py', 'tools/compile/prims/warp_prims.v']:
        sources[name] = b'fixture-source'
    for arch, prims in a.hosted.ARCHES.items():
        meta = {'name': arch, 'macro': 'macro/'+arch, 'arch_version': 2+prims}
        if prims:
            meta['primitives'] = {'wp_timer': 2}
        sources['arch/'+arch+'/arch.yaml'] = yaml.safe_dump(meta).encode()
        sources['arch/'+arch+'/pins.csv'] = b'fixture pins'
        sources['macro/'+arch+'/fabulous/bitStreamSpec.bin'] = b'fixture specification'
        sources['macro/'+arch+'/fabulous/.FABulous/placement_estimate.txt'] = b'fixture timing'
    class MemoryInputs:
        def __init__(self, revision, *args):
            assert revision == REV
        def expected_paths(self):
            return set(sources)
        def read(self, name):
            return sources[a.relative_name(name)]
    monkeypatch.setattr(a, 'GitInputs', MemoryInputs)
    tools = {'yosys': 'Yosys 0.66+179 e74db6dea', 'nextpnr-generic': 'nextpnr-0.11.1-34-gc4fbb55a', 'bitgen': 'tools/compile/bitgen.py'}
    result = dict(commit=REV, workflow_run=RUN, workflow_attempt='1', passed=True,
                  inputs_unchanged=True, physical_acceptance=False, timing_acceptance=False,
                  tiles_revision=a.TILES_REV, input_sha256={n: a.digest(b) for n,b in sources.items()},
                  tools=tools, tool_sha256=a.TOOL_HASHES.copy(), assessment_clock_mhz=50,
                  timing_corner=a.hosted.compiler.SLOW_CORNER, cases={})
    for arch, prims in a.hosted.ARCHES.items():
        meta = yaml.safe_load(sources['arch/'+arch+'/arch.yaml'])
        for design in a.hosted.DESIGNS:
            name = arch+'__'+design
            folder = tmp_path/name
            folder.mkdir()
            spec = yaml.safe_load(sources['protocols/'+design+'/pins.yaml'])
            params = dict(spec['params'], PRIMS=prims)
            fits = design != 'i2c_target'
            cell = {'type':'LUT4','connections':{'O':[1]},'port_directions':{'O':'output'}}
            dump(folder/'design.json', {'modules':{'warp_top':{'ports':{},'cells':{str(i):cell for i in range(1 if fits else 124)}}}})
            (folder/'synth.ys').write_text(a.hosted.compiler.chparam(params,spec['top'])+'\n')
            row = dict(design=design, arch=arch, params=params, seed=1, tools=tools,
                       timing_corner=a.hosted.compiler.SLOW_CORNER, fits=fits,
                       synthesis_estimate=a.hosted.compiler.cell_estimate(folder/'design.json','warp_top'))
            dump(folder/'case.json', row)
            if fits:
                (folder/'pnr.log').write_text('Info: FABULOUS_LC: 1/ 96 1%\nMax frequency for clock clk: 60.0 MHz\n')
                util,fmax=a.hosted.compiler.parse_pnr_log(folder/'pnr.log')
                from host.protocol import SYNC_WORD
                bf=a.hosted.BitFile(2+prims,[SYNC_WORD,1<<20]);image=folder/(spec['top']+'.wbit');bf.save(image)
                expected={n for n in sources if n.startswith('protocols/'+design+'/')}
                expected.update({'arch/'+arch+'/arch.yaml','arch/'+arch+'/pins.csv',
                    'macro/'+arch+'/fabulous/bitStreamSpec.bin','macro/'+arch+'/fabulous/.FABulous/placement_estimate.txt',
                    'tools/compile/compile.py','tools/compile/bitfile.py','tools/compile/bitgen.py'})
                if prims:expected.add('tools/compile/prims/warp_prims.v')
                dump(folder/'report.json',dict(design=spec['top'],params=params,arch=arch,
                    timing_corner=row['timing_corner'],tools=tools,build_options={'seed':1},utilisation=util,
                    fmax_mhz=fmax,words=2,arch_version=f'0x{bf.arch_version:04X}',crc32=f'0x{bf.crc:08X}',
                    provenance={'bitfile_sha256':a.digest(image.read_bytes()),'inputs':[
                        {'path':a.RUNNER_PREFIX+n,'sha256':a.digest(sources[n])} for n in sorted(expected)]}))
            else:
                native="Info: FABULOUS_LC: 124/ 96 129%\nERROR: Unable to place cell 'x', no BELs remaining\n"
                (folder/'pnr_stdout.log').write_text(native)
                util,_=a.hosted.compiler.parse_pnr_log(folder/'pnr_stdout.log')
                dump(folder/'failure.json',dict(stage='place_route',arch=arch,seed=1,tools=tools,
                    diagnosis=a.hosted.compiler.diagnose_pnr_failure(native,util)))
            result['cases'][name]=a.hosted.validate_case(folder,design,arch,source_spec=spec,source_arch=meta,
                read_input=lambda path:sources[path[len(a.RUNNER_PREFIX):]])
    dump(tmp_path/'result.json',result)
    return tmp_path,result,sources


def verify(path):
    return a.audit(path,revision=REV,run_id=RUN,attempt=1)


def test_moved_bundle_native_evidence_verified_without_worktree_specs(bundle,monkeypatch):
    path,_,_=bundle
    monkeypatch.setattr(a.hosted,'ROOT',Path('/nonexistent-worktree'))
    result=verify(path)
    assert result['verified'] and len(result['cases'])==8 and result['verified_images']==6


def test_missing_explicit_primitives_in_exact_source_rejected(bundle):
    path,result,sources=bundle
    name='protocols/uart/pins.yaml'
    spec=yaml.safe_load(sources[name]);spec['params'].pop('PRIMS')
    sources[name]=yaml.safe_dump(spec).encode()
    result['input_sha256'][name]=a.digest(sources[name])
    dump(path/'result.json',result)
    with pytest.raises(ValueError,match='Missing explicit primitive selection'):verify(path)


def test_missing_explicit_primitives_in_hosted_default_spec_rejected(bundle,tmp_path,monkeypatch):
    path,_,sources=bundle
    root=tmp_path/'separate-worktree';pins=root/'protocols/uart/pins.yaml';pins.parent.mkdir(parents=True)
    spec=yaml.safe_load(sources['protocols/uart/pins.yaml']);spec['params'].pop('PRIMS')
    pins.write_text(yaml.safe_dump(spec));monkeypatch.setattr(a.hosted,'ROOT',root)
    with pytest.raises(ValueError,match='Missing explicit primitive selection'):
        a.hosted.validate_case(path/'warp_g0__uart','uart','warp_g0')


@pytest.mark.parametrize('field,value',[('commit','b'*40),('workflow_run','9'),('workflow_attempt','2'),('passed',False)])
def test_run_identity_and_status_must_match(bundle,field,value):
    path,result,_=bundle;result[field]=value;dump(path/'result.json',result)
    with pytest.raises(ValueError):verify(path)


@pytest.mark.parametrize('attack',['missing_input','changed_input','missing_case','unknown_case','tool_hash'])
def test_incomplete_or_changed_identity_rejected(bundle,attack):
    path,result,_=bundle
    if attack=='missing_input':result['input_sha256'].pop(next(iter(result['input_sha256'])))
    elif attack=='changed_input':result['input_sha256'][next(iter(result['input_sha256']))]='0'*64
    elif attack=='missing_case':result['cases'].pop(next(iter(result['cases'])))
    elif attack=='unknown_case':result['cases']['warp_g0__heldout']={}
    else:result['tool_sha256']['yosys']='0'*64
    dump(path/'result.json',result)
    with pytest.raises(ValueError):verify(path)


def test_missing_provenance_rejected_even_after_artifact_rehash(bundle):
    path,result,_=bundle;p=path/'warp_g0__uart'/'report.json';report=json.loads(p.read_text());report['provenance']['inputs'].pop();dump(p,report)
    result['cases']['warp_g0__uart']['artifact_sha256']['report.json']=a.digest(p.read_bytes());dump(path/'result.json',result)
    with pytest.raises(ValueError,match='provenance'):verify(path)


def test_corrupt_emitted_image_rejected(bundle):
    path,_,_=bundle;image=path/'warp_g0__uart'/'uart_top.wbit';image.write_bytes(image.read_bytes()[:-1]+b'\x01')
    with pytest.raises(ValueError):verify(path)


def test_native_usage_corruption_rejected_even_when_artifact_hash_updated(bundle):
    path,result,_=bundle;log=path/'warp_g0__uart'/'pnr.log'
    log.write_text(log.read_text().replace('1/ 96','2/ 96'))
    result['cases']['warp_g0__uart']['artifact_sha256']['pnr.log']=a.digest(log.read_bytes())
    dump(path/'result.json',result)
    with pytest.raises(ValueError,match='usage/timing'):verify(path)


def test_unlisted_retained_case_file_rejected(bundle):
    path,_,_=bundle;(path/'warp_g0__uart'/'unexpected.txt').write_text('not authenticated')
    with pytest.raises(ValueError,match='recorded case'):verify(path)


def test_unknown_original_absolute_provenance_path_rejected(bundle):
    path,result,_=bundle;p=path/'warp_g0__uart'/'report.json';report=json.loads(p.read_text())
    report['provenance']['inputs'][0]['path']='/tmp/untrusted-current-file'
    dump(p,report);result['cases']['warp_g0__uart']['artifact_sha256']['report.json']=a.digest(p.read_bytes());dump(path/'result.json',result)
    with pytest.raises(ValueError,match='runner input path'):verify(path)


@pytest.mark.parametrize('name',['../protocols/uart/pins.yaml','/tmp/input','protocols/uart/../uart/pins.yaml'])
def test_noncanonical_input_paths_rejected(name):
    with pytest.raises(ValueError):a.relative_name(name)


def test_git_reader_refuses_unapproved_protocol_before_reading_blob():
    reader=a.GitInputs(REV)
    with pytest.raises(ValueError,match='Unapproved protocol'):reader.read('protocols/heldout/user.v')


def test_unknown_setup_failure_is_not_nonfit_even_after_rehash(bundle):
    path,result,_=bundle;folder=path/'warp_g0__i2c_target';log=folder/'pnr_stdout.log';native=log.read_text()+'ERROR: Missing architecture file\n';log.write_text(native)
    fail=json.loads((folder/'failure.json').read_text());util,_=a.hosted.compiler.parse_pnr_log(log);fail['diagnosis']=a.hosted.compiler.diagnose_pnr_failure(native,util);dump(folder/'failure.json',fail)
    with pytest.raises(ValueError,match='unknown/setup'):verify(path)


def test_supervisor_adapter_requires_explicit_identity(bundle):
    path,_,_=bundle
    with pytest.raises(ValueError):supervisor.validate_evidence(path,'architecture',REV)
    assert supervisor.validate_evidence(path,'architecture',REV,run_id=RUN,attempt=1)['architecture']['verified']
    assert set(supervisor.TASKS)=={'uart-phase','active-cancel','c-host','compiler-seeds'}
