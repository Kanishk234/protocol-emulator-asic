"""Evidence rejection tests only; no local EDA."""
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_arch_comparison as evidence


def test_workflow_setup_scripts_can_be_invoked_from_checkout():
    workflow = yaml.safe_load((evidence.ROOT/'.github/workflows/arch_comparison_evidence.yaml').read_text())
    count = 0
    for step in workflow['jobs']['compare']['steps']:
        for line in step.get('run', '').splitlines():
            words = line.strip().split()
            if not words:
                continue
            if words[0].startswith('scripts/'):
                assert os.access(evidence.ROOT/words[0], os.X_OK), words[0]
                count += 1
            elif words[0] == 'bash' and len(words) > 1 and words[1].startswith('scripts/'):
                assert (evidence.ROOT/words[1]).is_file(), words[1]
                count += 1
    assert count == 2


def failed_case(tmp_path, monkeypatch, category='resource_capacity'):
    row = dict(design='uart', arch='warp_g0', params=evidence.parameters('uart', 'warp_g0'),
               timing_corner=evidence.compiler.SLOW_CORNER, seed=1, fits=False,
               synthesis_estimate={'lcs': 124}, tools={'yosys': 'fixture'})
    (tmp_path/'case.json').write_text(json.dumps(row))
    (tmp_path/'design.json').write_text('{}')
    (tmp_path/'synth.ys').write_text(evidence.compiler.chparam(row['params'], 'uart_top')+'\n')
    monkeypatch.setattr(evidence.compiler, 'cell_estimate', lambda *args: {'lcs': 124})
    logs = {
        'resource_capacity': 'Info: FABULOUS_LC: 124/ 96 129%\nERROR: Unable to place cell x\n',
        'placement': 'Info: FABULOUS_LC: 80/ 96 83%\nERROR: Unable to place cell x\n',
        'unknown': 'ERROR: Missing architecture file\n',
        'routing': 'ERROR: failed to route net x\n',
    }
    native = logs[category]
    (tmp_path/'pnr_stdout.log').write_text(native)
    util, _ = evidence.compiler.parse_pnr_log(tmp_path/'pnr_stdout.log')
    failure = dict(stage='place_route', arch='warp_g0', seed=1, tools=row['tools'],
                   diagnosis=evidence.compiler.diagnose_pnr_failure(native, util))
    (tmp_path/'failure.json').write_text(json.dumps(failure))
    return row


def test_pairs_change_only_primitive_selection():
    for design in evidence.DESIGNS:
        plain = evidence.parameters(design, 'warp_g0')
        hard = evidence.parameters(design, 'warp_g1')
        assert {key for key in plain if plain[key] != hard[key]} == {'PRIMS'}


@pytest.mark.parametrize('design,arch', [('heldout', 'warp_g0'), ('uart', 'unknown')])
def test_unapproved_inputs_rejected(design, arch):
    with pytest.raises(ValueError):
        evidence.parameters(design, arch)


@pytest.mark.parametrize('category', ['resource_capacity', 'placement'])
def test_proven_native_nonfit_remains_estimate(tmp_path, monkeypatch, category):
    failed_case(tmp_path, monkeypatch, category)
    result = evidence.validate_case(tmp_path, 'uart', 'warp_g0')
    assert result['failure_category'] == category
    assert result['placed_utilisation'] is None
    assert result['synthesis_capacity_estimate']['lcs'] == 124


@pytest.mark.parametrize('category', ['unknown', 'routing'])
def test_other_errors_are_not_expected_nonfit(tmp_path, monkeypatch, category):
    failed_case(tmp_path, monkeypatch, category)
    with pytest.raises(ValueError, match='native capacity/placement'):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


def test_failure_requires_fatal_not_just_high_demand(tmp_path, monkeypatch):
    failed_case(tmp_path, monkeypatch)
    (tmp_path/'pnr_stdout.log').write_text('Info: FABULOUS_LC: 124/ 96 129%\n')
    with pytest.raises(ValueError):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


@pytest.mark.parametrize('extra', [
    'ERROR: Missing architecture file', 'ERROR: ImportError: cannot import architecture',
    'FATAL: Segmentation fault', 'ERROR: failed to route net x', 'ERROR: unknown failure',
])
@pytest.mark.parametrize('keep_placement_fatal', [False, True])
def test_overcapacity_never_masks_unrelated_fatal(tmp_path, monkeypatch, extra, keep_placement_fatal):
    failed_case(tmp_path, monkeypatch)
    native = 'Info: FABULOUS_LC: 124/ 96 129%\n'
    if keep_placement_fatal:
        native += 'ERROR: Unable to place cell x\n'
    native += extra+'\n'
    (tmp_path/'pnr_stdout.log').write_text(native)
    path = tmp_path/'failure.json'
    failure = json.loads(path.read_text())
    util, _ = evidence.compiler.parse_pnr_log(tmp_path/'pnr_stdout.log')
    failure['diagnosis'] = evidence.compiler.diagnose_pnr_failure(native, util)
    assert failure['diagnosis']['category'] == 'resource_capacity'
    path.write_text(json.dumps(failure))
    with pytest.raises(ValueError, match='unknown/setup fatal'):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


@pytest.mark.parametrize('artifact', ['uart_top.wbit', 'report.json'])
def test_nonfit_rejects_stale_success(tmp_path, monkeypatch, artifact):
    failed_case(tmp_path, monkeypatch)
    (tmp_path/artifact).write_text('stale')
    with pytest.raises(ValueError, match='successful artifacts'):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


def test_parameters_cannot_silently_drift(tmp_path, monkeypatch):
    row = failed_case(tmp_path, monkeypatch)
    row['params']['DIV'] += 1
    (tmp_path/'case.json').write_text(json.dumps(row))
    with pytest.raises(ValueError, match='parameters'):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


def test_subprocess_nonzero_fails_campaign(tmp_path, monkeypatch):
    monkeypatch.setattr(evidence.subprocess, 'Popen', lambda *args, **kwargs: SimpleNamespace(wait=lambda **kw: 2))
    with pytest.raises(RuntimeError, match='worker failed'):
        evidence.run_bounded(['false'], tmp_path/'worker.log')


def test_timeout_terminates_process_group(tmp_path, monkeypatch):
    calls = []
    def wait(**kwargs):
        if kwargs.get('timeout') == 600:
            raise subprocess.TimeoutExpired('worker', 600)
        return 0
    monkeypatch.setattr(evidence.subprocess, 'Popen', lambda *args, **kwargs: SimpleNamespace(pid=123, wait=wait))
    monkeypatch.setattr(evidence.os, 'killpg', lambda pid, sig: calls.append((pid, sig)))
    with pytest.raises(subprocess.TimeoutExpired):
        evidence.run_bounded(['worker'], tmp_path/'worker.log')
    assert [sig for _, sig in calls] == [evidence.signal.SIGTERM, evidence.signal.SIGKILL]


def successful_case(tmp_path, monkeypatch):
    row = failed_case(tmp_path, monkeypatch)
    row['fits'] = True
    (tmp_path/'case.json').write_text(json.dumps(row))
    (tmp_path/'failure.json').unlink()
    (tmp_path/'pnr.log').write_text('Info: FABULOUS_LC: 80/ 96 83%\nMax frequency for clock clk: 60.0 MHz\n')
    util, fmax = evidence.compiler.parse_pnr_log(tmp_path/'pnr.log')
    from host.protocol import SYNC_WORD
    image = tmp_path/'uart_top.wbit'
    bitfile = evidence.BitFile(2, [SYNC_WORD, 1 << 20])
    bitfile.save(image)
    report = dict(design='uart_top', arch='warp_g0', params=row['params'],
        timing_corner=evidence.compiler.SLOW_CORNER, tools=row['tools'], build_options={'seed': 1},
        utilisation=util, fmax_mhz=fmax, words=2, arch_version='0x0002',
        crc32=f'0x{bitfile.crc:08X}', provenance={'bitfile_sha256': evidence.sha(image),
        'inputs': [{'path': str(tmp_path/'synth.ys'), 'sha256': evidence.sha(tmp_path/'synth.ys')}]})
    (tmp_path/'report.json').write_text(json.dumps(report))


def test_success_checks_actual_native_usage_and_image(tmp_path, monkeypatch):
    successful_case(tmp_path, monkeypatch)
    row = evidence.validate_case(tmp_path, 'uart', 'warp_g0')
    assert row['placed_utilisation']['FABULOUS_LC']['used'] == 80
    assert row['compiler_fmax_mhz'] == 60


@pytest.mark.parametrize('corruption', ['image', 'report', 'synth'])
def test_success_rejects_image_report_or_actual_parameter_corruption(tmp_path, monkeypatch, corruption):
    successful_case(tmp_path, monkeypatch)
    if corruption == 'image':
        image = tmp_path/'uart_top.wbit'
        image.write_bytes(image.read_bytes()[:-1]+b'\x01')
    elif corruption == 'synth':
        (tmp_path/'synth.ys').write_text('chparam -set PRIMS 1 uart_top\n')
    else:
        path = tmp_path/'report.json'
        report = json.loads(path.read_text())
        report['utilisation']['FABULOUS_LC']['used'] = 79
        path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')


@pytest.mark.parametrize('wrong', ['top', 'architecture_version'])
def test_success_independently_checks_top_and_architecture_identity(tmp_path, monkeypatch, wrong):
    successful_case(tmp_path, monkeypatch)
    path = tmp_path/'report.json'
    report = json.loads(path.read_text())
    if wrong == 'top':
        report['design'] = 'wrong_top'
    else:
        image = tmp_path/'uart_top.wbit'
        bitfile = evidence.BitFile.load(image)
        bitfile.arch_version = 3
        bitfile.save(image)
        report['arch_version'] = '0x0003'
        report['provenance']['bitfile_sha256'] = evidence.sha(image)
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        evidence.validate_case(tmp_path, 'uart', 'warp_g0')
