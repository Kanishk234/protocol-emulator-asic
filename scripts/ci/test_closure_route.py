from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import pytest

from closure_route import (SOURCE_RUN, SOURCE_SHA, IMAGE, IMAGE_DIGEST, CONFIG_SHA,
                           PDK, TOOLS, provenance, unpack, timing_gate, restore)
from postgrt_timing import CORNERS
from test_stock_screen_gate import fixture as screen_fixture


def context():
    return (dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main',
                 path='.github/workflows/gds-official-dev4-hold125-screen.yaml',
                 status='completed', conclusion='success', run_attempt=1),
            dict(name=f'official-dev4-hold125-{SOURCE_RUN}', expired=False,
                 workflow_run=dict(id=SOURCE_RUN, head_sha=SOURCE_SHA), digest='sha256:' + 'a' * 64))


def test_exact_completed_source_admitted():
    provenance(*context())


@pytest.mark.parametrize('key,value', [('id', 1), ('head_sha', 'foreign'),
    ('head_branch', 'other'), ('path', '.github/workflows/gds.yaml'),
    ('status', 'in_progress'), ('conclusion', 'failure'), ('run_attempt', 2)])
def test_foreign_failed_running_or_rerun_source_rejected(key, value):
    run, artifact = context()
    run[key] = value
    with pytest.raises(ValueError, match='exact successful'):
        provenance(run, artifact)


@pytest.mark.parametrize('mutation', ['name', 'expired', 'foreignrun', 'foreignsha', 'digest'])
def test_wrong_artifact_rejected(mutation):
    run, artifact = context()
    if mutation == 'name': artifact['name'] = 'other'
    if mutation == 'expired': artifact['expired'] = True
    if mutation == 'foreignrun': artifact['workflow_run']['id'] = 1
    if mutation == 'foreignsha': artifact['workflow_run']['head_sha'] = 'other'
    if mutation == 'digest': artifact['digest'] = None
    with pytest.raises(ValueError): provenance(run, artifact)


@pytest.mark.parametrize('name', ['runs/checkpoint.json', '../escape', '/absolute', 'scripts/ci/run.py', 'runs/../escape'])
def test_digest_and_archive_scope(tmp_path, name):
    archive = tmp_path / 'source.zip'
    with zipfile.ZipFile(archive, 'w') as bundle: bundle.writestr(name, 'payload')
    artifact = {'digest': 'sha256:' + hashlib.sha256(archive.read_bytes()).hexdigest()}
    output = tmp_path / 'frozen'
    if name == 'runs/checkpoint.json':
        unpack(archive, artifact, output)
        assert (output / name).read_text() == 'payload'
    else:
        with pytest.raises(ValueError, match='Unsafe'): unpack(archive, artifact, output)
        assert not output.exists()
    with pytest.raises(ValueError, match='digest mismatch'):
        unpack(archive, {'digest': 'sha256:' + '0' * 64}, tmp_path / 'wrong')


def timing():
    result = {'corners': {}}
    for corner in CORNERS:
        row = {f'timing__setup__ws__corner:{corner}': 0,
               f'timing__hold__ws__corner:{corner}': 0.05}
        row.update({f'design__max_{k}_violation__count__corner:{corner}': 0
                    for k in ('slew', 'cap', 'fanout')})
        result['corners'][corner] = {'before': row, 'after': deepcopy(row)}
    return result


def test_timing_exact_boundary_admitted(): timing_gate(timing())


@pytest.mark.parametrize('metric,value', [('setup', -0.000001), ('hold', 0.049999),
    ('hold', float('nan')), ('hold', True), ('slew', 1), ('cap', 1), ('fanout', 1)])
def test_fresh_timing_rejects_bad_values_on_either_replay(metric, value):
    data = timing(); corner = CORNERS[0]
    key = f'timing__{metric}__ws__corner:{corner}' if metric in ('setup', 'hold') else f'design__max_{metric}_violation__count__corner:{corner}'
    data['corners'][corner]['after'][key] = value
    with pytest.raises(ValueError): timing_gate(data)


def restored_fixture(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    root = tmp_path / 'runner'; root.mkdir()
    src = root / 'src'; src.mkdir()
    (root / 'macro').mkdir()
    (src / 'trw_chip.v').write_text('frozen hardware')
    (root / 'macro/view.lef').write_text('frozen macro')
    config = json.loads((repo / 'spikes/phase2_stock_flow/strict_project_config.json').read_text())
    profiles = json.loads((repo / 'spikes/phase2_stock_flow/stock_control_profiles.json').read_text())
    config.update(profiles['profiles']['rtl_shared_minbuf2_host_idle_ff']['changes'])
    config.update(CTS_SINK_CLUSTERING_MAX_DIAMETER=75, GRT_RESIZER_HOLD_SLACK_MARGIN=0.125)
    blob = json.dumps(config, indent=2) + '\n'
    assert hashlib.sha256(blob.encode()).hexdigest() == CONFIG_SHA
    (src / 'config.json').write_text(blob)
    (src / 'config_merged.json').write_text(json.dumps(dict(DIE_AREA='0 0 1724.16 710.64', CLOCK_PERIOD=20, RT_MAX_LAYER='Metal4')))
    (src / 'signoff.sdc').write_text('unchanged timing constraints')
    (root / 'info.yaml').write_text('same frozen metadata')
    physical, _ = screen_fixture(root / 'runs')
    physical.rename(root / 'runs/stock-official-baseline')
    (root / 'runs/audit').rename(root / 'runs/stock-corner-audit')
    # Use the final runner path in all physical state and audit receipts.
    for path in (root / 'runs').rglob('*.json'):
        path.write_text(path.read_text().replace('/runs/physical/', '/runs/stock-official-baseline/'))
    source = next((root / 'runs/stock-official-baseline').glob('*-openroad-stamidpnr-3/state_out.json'))
    state = json.loads(source.read_text())
    audit = root / 'runs/stock-corner-audit/read_only_audit.json'
    data = json.loads(audit.read_text())
    data['unchanged_physical_view_hashes'] = {
        name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
        for name in data['unchanged_physical_view_hashes']}
    audit.write_text(json.dumps(data))
    signoff = root / 'runs/stock-signoff-estimate'; signoff.mkdir()
    paths = [source, src / 'signoff.sdc'] + [Path(state[k]) for k in ('odb', 'def', 'nl', 'pnl', 'sdc')]
    (signoff / 'qualification.json').write_text(json.dumps(dict(qualified=True, failures=[],
        unchanged_source_hashes={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})))
    (signoff / 'comparison.json').write_text(json.dumps(timing()))
    expected = tmp_path / 'expected'; expected.mkdir()
    frozen = tmp_path / 'frozen'; frozen.mkdir()
    for target in (expected, frozen):
        for folder in ('src', 'macro'): shutil.copytree(root / folder, target / folder)
        shutil.copy2(root / 'info.yaml', target / 'info.yaml')
    shutil.move(root / 'runs', frozen / 'runs')
    (frozen / 'compatibility-engine.json').write_text(json.dumps(dict(librelane='3.1.0.dev4', pdk_revision=PDK, tools_sha=TOOLS)))
    (frozen / 'compatibility-image.json').write_text(json.dumps([{'RepoDigests': [IMAGE.rsplit(':', 1)[0] + '@' + IMAGE_DIGEST]}]))
    return root, frozen, expected


def test_restores_exact_views_and_rechecks_raw_gates(tmp_path):
    root, frozen, expected = restored_fixture(tmp_path)
    source = restore(root, frozen, expected)
    assert source.is_file()
    receipt = json.loads((root / 'runs/closure-restoration.json').read_text())
    assert receipt['qualified'] is True and receipt['saved_state_rewritten'] is False


def test_real_mixed_relative_state_and_absolute_native_views(tmp_path):
    root, frozen, expected = restored_fixture(tmp_path)
    audit = frozen / 'runs/stock-corner-audit/read_only_audit.json'
    data = json.loads(audit.read_text())
    absolute_state = data['source_state']
    relative_state = str(Path(absolute_state).relative_to(root))
    data['source_state'] = relative_state
    hashes = data['unchanged_physical_view_hashes']
    hashes[relative_state] = hashes.pop(absolute_state)
    audit.write_text(json.dumps(data))
    signoff = frozen / 'runs/stock-signoff-estimate/qualification.json'
    data = json.loads(signoff.read_text())
    hashes = data['unchanged_source_hashes']
    hashes[relative_state] = hashes.pop(absolute_state)
    hashes['src/signoff.sdc'] = hashes.pop(str(root / 'src/signoff.sdc'))
    signoff.write_text(json.dumps(data))
    before = {str(p.relative_to(frozen)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (frozen / 'runs').rglob('*') if p.is_file()}
    restore(root, frozen, expected)
    assert all(hashlib.sha256((root / name).read_bytes()).hexdigest() == sha
               for name, sha in before.items())


@pytest.mark.parametrize('mutation', ['hardware', 'metadata', 'runner', 'signoff', 'rawtiming', 'rawantenna'])
def test_altered_source_or_saved_acceptance_rejected(tmp_path, mutation):
    root, frozen, expected = restored_fixture(tmp_path)
    if mutation == 'hardware': (frozen / 'src/trw_chip.v').write_text('changed')
    if mutation == 'metadata': (frozen / 'info.yaml').write_text('wrong geometry')
    if mutation == 'runner':
        p = frozen / 'runs/stock-corner-audit/read_only_audit.json'
        data = json.loads(p.read_text()); data['source_state'] = '/other/runner/state.json'; p.write_text(json.dumps(data))
    if mutation == 'signoff':
        p = frozen / 'runs/stock-signoff-estimate/qualification.json'
        data = json.loads(p.read_text()); data['qualified'] = False; p.write_text(json.dumps(data))
    if mutation == 'rawtiming':
        p = frozen / 'runs/stock-signoff-estimate/comparison.json'
        data = json.loads(p.read_text()); data['corners'][CORNERS[0]]['after'][f'timing__hold__ws__corner:{CORNERS[0]}'] = -1; p.write_text(json.dumps(data))
    if mutation == 'rawantenna':
        p = next((frozen / 'runs/stock-corner-audit/fresh-antenna').glob('*-openroad-checkantennas/or_metrics_out.json'))
        p.write_text(json.dumps({'antenna__violating__nets': 1, 'antenna__violating__pins': 1}))
    with pytest.raises(ValueError): restore(root, frozen, expected)
