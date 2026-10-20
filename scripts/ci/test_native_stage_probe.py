import copy
import json
from pathlib import Path

import pytest
import yaml
import native_stage_probe as probe


def source():
    return dict(id=probe.SOURCE_RUN, head_sha=probe.SOURCE_SHA, head_branch='main',
                conclusion='failure', path='.github/workflows/gds-native-tx-cursor-setup-reserve-screen.yaml')


@pytest.mark.parametrize('fault', [None, 'id', 'head_sha', 'head_branch', 'conclusion', 'path', 'hash', 'clock'])
def test_only_exact_failed_source_is_diagnostic_input(monkeypatch, fault):
    run = source(); config = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56)
    monkeypatch.setattr(probe, 'digest', lambda p: 'wrong' if fault == 'hash' else probe.HASHES[p.name])
    if fault in run:
        run[fault] = 'wrong'
    if fault == 'clock':
        config['CLOCK_PERIOD'] = 21
    if fault:
        with pytest.raises(ValueError):
            probe.validate(run, config)
    else:
        probe.validate(run, config)


def test_diagnostic_replaces_inherited_flow_with_sta_only():
    original = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                    meta={'version': 1, 'flow': 'Classic'}, GRT_RESIZER_HOLD_SLACK_MARGIN=.125)
    saved = copy.deepcopy(original)
    result = probe.stage_config(original)
    assert original == saved
    assert result['meta'] == {'version': 1, 'flow': ['OpenROAD.STAMidPNR']}
    assert result['PNR_CORNERS'] == [probe.CORNER]
    assert result['CLOCK_PERIOD'] == 20
    assert result['GRT_RESIZER_HOLD_SLACK_MARGIN'] == .125
    assert result['PNR_SDC_FILE'] == result['SIGNOFF_SDC_FILE']


def test_workflow_downloads_failed_source_and_never_runs_route():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-tx-stage-diagnosis.yaml').read_text())['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == probe.SOURCE_RUN
    assert download['with']['name'].endswith(str(probe.SOURCE_RUN))
    commands = '\n'.join(s.get('run', '') for s in job['steps'])
    assert 'native_stage_probe.py' in commands
    assert 'native_arithmetic_screen.py' not in commands
    assert '--prepare' not in commands
    tcl = (root/'scripts/ci/native_stage_probe.tcl').read_text()
    assert 'repair_design' not in tcl and 'repair_timing' not in tcl
    assert 'detailed_route' not in tcl
    for net in ['_09431_', '_21816_']:
        assert net in tcl


def test_main_preserves_relative_macro_paths_through_every_stage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('PDK_ROOT', '/pdk')
    Path('src').mkdir(); Path('macro').mkdir()
    macro = Path('macro/sram.gds'); macro.write_bytes(b'unchanged macro')
    config = dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56,
                  MACROS={'sram': {'gds': ['dir::../macro/sram.gds']}})
    Path('src/config_native_stock.json').write_text(json.dumps(config))
    # Isolate the fixed receipt location; provenance itself is tested above.
    original_read = Path.read_text
    def read(path, *args, **kwargs):
        if str(path) == '/tmp/native-source-run.json':
            return json.dumps(source())
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', read)
    monkeypatch.setattr(probe, 'validate', lambda *args: None)
    for stage in probe.STAGES:
        folder = Path('runs/native-stock-screen/flow')/stage
        folder.mkdir(parents=True)
        odb = folder/'tt_um_tripwire.odb'; odb.write_bytes(stage.encode())
        (folder/'state_out.json').write_text(json.dumps({'odb': str(odb.resolve())}))
    calls = []
    def run(command, **kwargs):
        path = Path(command[-1])
        assert path.parent == Path('src')
        resolved = json.loads(path.read_text())
        relative = resolved['MACROS']['sram']['gds'][0].removeprefix('dir::')
        assert (path.parent/relative).resolve() == macro.resolve()
        assert (path.parent/relative).read_bytes() == b'unchanged macro'
        assert resolved['meta']['flow'] == ['OpenROAD.STAMidPNR']
        out = Path(command[command.index('--force-run-dir')+1])/'1-openroad-stamidpnr'
        out.mkdir()
        (out/'electrical_margin.rpt').write_text('fixture')
        (out/'capture_setup.rpt').write_text('fixture')
        calls.append(command)
    monkeypatch.setattr(probe.subprocess, 'run', run)
    monkeypatch.setattr(probe, 'capture_setup', lambda text: 3.0)
    monkeypatch.setattr(probe, 'parse', lambda text: (probe.CORNER, {'nets': {'_09431_': {}, '_21816_': {}}}))
    probe.main()
    assert len(calls) == len(probe.STAGES) == 5
    receipt = json.loads(Path('runs/native-stage-probe/diagnosis.json').read_text())
    assert receipt['qualified'] is False and receipt['repair_performed'] is False
    assert set(receipt['stages']) == set(probe.STAGES)
