"""Adversarial checks for the new G1 census, without invoking EDA."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'test_internal'))
spec = importlib.util.spec_from_file_location('fresh_baseline', ROOT / 'test_internal/cloud_fresh_baseline.py')
campaign = importlib.util.module_from_spec(spec)
spec.loader.exec_module(campaign)


def test_explicit_matrix_and_dependencies():
    assert len(set(campaign.CASES)) == 11
    for name in campaign.CASES:
        pins, sources, params = campaign.specification(name)
        assert pins.is_file() and all(p.is_file() for p in sources)
        if name.startswith('uart_spi'):
            assert len(sources) == 7
            assert params['UART_PRIMS'] == int(name[-2])
            assert params['SPI_PRIMS'] == int(name[-1])
    with pytest.raises(ValueError):
        campaign.specification('arbitrary_protocol')


@pytest.fixture
def rejected(tmp_path, monkeypatch):
    name = 'uart_spi_11'
    pins, _, params = campaign.specification(name)
    top = campaign.yaml.safe_load(pins.read_text())['top']
    estimate = {'timers': 3, 'shifts': 3}
    tools = {'yosys': 'test', 'nextpnr-generic': 'test'}
    diagnosis = dict(category='resource_capacity', fatal_messages=[
        'ERROR: Unable to place cell foo no BELs remaining FAB_TIMER'],
        over_capacity=['FAB_TIMER: 3/2'], advice='test')
    row = dict(name=name, params=params, seed=1, fits=False, tools=tools,
               synthesis_estimate=estimate)
    failure = dict(stage='place_route', arch='warp_g1', seed=1, tools=tools,
                   diagnosis=diagnosis)
    (tmp_path / 'synth.ys').write_text(campaign.compiler.chparam(params, top) + '\n')
    (tmp_path / 'pnr_stdout.log').write_text('native diagnostic')
    monkeypatch.setattr(campaign.compiler, 'cell_estimate', lambda *args: estimate)
    monkeypatch.setattr(campaign.compiler, 'parse_pnr_log', lambda *args: ({}, None))
    monkeypatch.setattr(campaign.compiler, 'diagnose_pnr_failure', lambda *args: diagnosis)
    def write():
        (tmp_path / 'case.json').write_text(json.dumps(row))
        (tmp_path / 'failure.json').write_text(json.dumps(failure))
    write()
    return tmp_path, name, row, failure, write


def test_genuine_rejection_retains_diagnosis(rejected):
    path, name, _, _, _ = rejected
    row = campaign.validate(path, name)
    assert row['placed_utilisation'] is None
    assert row['native_diagnosis']['over_capacity'] == ['FAB_TIMER: 3/2']


@pytest.mark.parametrize('field,value', [('seed', 2), ('name', 'uart'), ('fits', 'false')])
def test_reject_changed_case(rejected, field, value):
    path, name, row, _, write = rejected
    row[field] = value
    write()
    with pytest.raises(ValueError):
        campaign.validate(path, name)


@pytest.mark.parametrize('field,value', [('stage', 'synthesis'), ('arch', 'other'), ('seed', 2)])
def test_reject_wrong_failure_identity(rejected, field, value):
    path, name, _, failure, write = rejected
    failure[field] = value
    write()
    with pytest.raises(ValueError):
        campaign.validate(path, name)


@pytest.mark.parametrize('category', ['unknown', 'routing'])
def test_unknown_or_routing_failure_is_not_capacity_result(rejected, category):
    path, name, _, failure, write = rejected
    failure['diagnosis']['category'] = category
    write()
    with pytest.raises(ValueError):
        campaign.validate(path, name)


def test_extra_setup_fatal_not_masked_by_resource_excess(rejected):
    path, name, _, failure, write = rejected
    failure['diagnosis']['fatal_messages'].append('ERROR: Cannot open architecture model')
    write()
    with pytest.raises(ValueError):
        campaign.validate(path, name)


@pytest.mark.parametrize('artifact', ['report.json', 'stale.wbit'])
def test_rejected_case_cannot_keep_successful_artifact(rejected, artifact):
    path, name, _, _, _ = rejected
    (path / artifact).write_text('stale')
    with pytest.raises(ValueError):
        campaign.validate(path, name)


def test_actual_synthesis_parameters_required(rejected):
    path, name, _, _, _ = rejected
    (path / 'synth.ys').write_text('different settings')
    with pytest.raises(ValueError):
        campaign.validate(path, name)


def test_no_local_measurement_or_spoofed_run(monkeypatch):
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    with pytest.raises(RuntimeError, match='hosted'):
        campaign.worker('uart', '/tmp/unused-warp-worker')
    with pytest.raises(RuntimeError, match='hosted'):
        campaign.main()

@pytest.fixture
def successful(tmp_path, monkeypatch):
    name = 'uart_spi_10'
    pins, sources, params = campaign.specification(name)
    top = campaign.yaml.safe_load(pins.read_text())['top']
    estimate = {'lcs': 100}
    tools = {'yosys': 'test', 'nextpnr-generic': 'test'}
    util = {'FABULOUS_LC': {'used': 80, 'available': 88}}
    image = tmp_path / 'concurrency.wbit'
    from host.protocol import SYNC_WORD
    bf = campaign.BitFile(3, [SYNC_WORD, 1, 2])
    bf.save(image)
    row = dict(name=name, params=params, seed=1, fits=True, tools=tools,
               synthesis_estimate=estimate)
    report = dict(params=params, design=top, arch='warp_g1', build_options={'seed': 1},
                  tools=tools, timing_corner=campaign.compiler.SLOW_CORNER,
                  utilisation=util, fmax_mhz=51.0, meets_50mhz=True, words=3,
                  crc32=f'0x{bf.crc:08X}', unmapped_inputs_tied_0=[], unmapped_outputs_open=[],
                  provenance={'inputs': [{'path': str(pins), 'sha256': campaign.sha(pins)}],
                              'bitfile_sha256': campaign.sha(image)})
    (tmp_path / 'synth.ys').write_text(campaign.compiler.chparam(params, top) + '\n')
    monkeypatch.setattr(campaign.compiler, 'cell_estimate', lambda *args: estimate)
    monkeypatch.setattr(campaign.compiler, 'parse_pnr_log', lambda *args: (util, 51.0))
    def write():
        (tmp_path / 'case.json').write_text(json.dumps(row))
        (tmp_path / 'report.json').write_text(json.dumps(report))
    write()
    return tmp_path, name, report, write


def test_success_checks_native_usage_and_image(successful):
    path, name, _, _ = successful
    assert campaign.validate(path, name)['model_fmax_mhz'] == 51.0


@pytest.mark.parametrize('mutation', ['image', 'params', 'fingerprint', 'unmapped', 'empty', 'clock'])
def test_tampered_success_is_rejected(successful, mutation):
    path, name, report, write = successful
    if mutation == 'image':
        report['provenance']['bitfile_sha256'] = '0' * 64
    elif mutation == 'params':
        report['params'] = {}
    elif mutation == 'fingerprint':
        report['provenance']['inputs'][0]['sha256'] = '0' * 64
    elif mutation == 'unmapped':
        report['unmapped_inputs_tied_0'] = ['h_wvalid']
    elif mutation == 'empty':
        report['provenance']['inputs'] = []
    else:
        report['meets_50mhz'] = False
    write()
    with pytest.raises(ValueError):
        campaign.validate(path, name)
