import hashlib
import json
from pathlib import Path

import pytest
import yaml

import native_incremental_route_control as trial
from test_native_no_final_grt_control import config


@pytest.mark.parametrize('bad_source', [False, True])
def test_source_checked_before_build_and_native_config_preserved(tmp_path, monkeypatch, bad_source):
    monkeypatch.chdir(tmp_path)
    Path('src').mkdir()
    original = dict(config(), GRT_RESIZER_RUN_GRT=True)
    Path('src/config_native_stock.json').write_text(json.dumps(original))
    source = Path('runs/native-stock-screen/flow')/trial.SOURCE_STAGE
    source.mkdir(parents=True)
    odb = source/'tt_um_tripwire.odb'
    odb.write_bytes(b'wrong' if bad_source else b'original')
    (source/'state_out.json').write_text(json.dumps({'odb': str(odb.resolve())}))
    monkeypatch.setattr(trial, 'SOURCE_ODB_HASH', hashlib.sha256(b'original').hexdigest())
    read_text = Path.read_text
    monkeypatch.setattr(Path, 'read_text', lambda p, *a, **kw:
        '{}' if str(p) == '/tmp/native-source-run.json' else read_text(p, *a, **kw))
    monkeypatch.setattr(trial, 'validate', lambda *a: None)
    builds = []
    monkeypatch.setattr(trial.subprocess, 'run', lambda args, **kw: builds.append(args))

    class ReachedNativeRepair(Exception):
        pass

    def run_step(cfg, state, output, steps):
        assert cfg == original
        assert state == source/'state_out.json'
        assert steps == ['OpenROAD.ResizerTimingPostGRT', 'OpenROAD.RepairAntennas']
        raise ReachedNativeRepair

    monkeypatch.setattr(trial, 'run_step', run_step)
    if bad_source:
        with pytest.raises(ValueError, match='database'):
            trial.main()
        assert not builds
    else:
        with pytest.raises(ReachedNativeRepair):
            trial.main()
        assert len(builds) == 1 and builds[0][:2] == ['docker', 'build']


def test_workflow_source_binding():
    root = Path(__file__).resolve().parents[2]
    job = yaml.safe_load((root/'.github/workflows/gds-native-incremental-route-control.yaml').read_text())['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))['with']
    assert download['run-id'] == trial.PROFILE['source_run']
    assert any(s.get('run') == 'python workflow-src/scripts/ci/native_incremental_route_control.py' for s in job['steps'])


def test_custom_image_metadata_preserves_measured_rejection():
    original = dict(qualified=False, diagnostic_only=True, custom_image=False,
                    checkpoint_measured_gates_pass=False,
                    estimated_margin_pass=False, capture_setup_minimum_ns={'slow': 3.030177})
    result = trial.record_control_image(original, 'tripwire-native-incremental-route:local')
    assert result['custom_image'] is True
    assert result['native_routing_modified'] is True
    assert result['capture_setup_minimum_ns'] == original['capture_setup_minimum_ns']
    assert result['checkpoint_measured_gates_pass'] is False
    assert original['custom_image'] is False
    with pytest.raises(ValueError):
        trial.record_control_image(dict(original, qualified=True), 'image')
