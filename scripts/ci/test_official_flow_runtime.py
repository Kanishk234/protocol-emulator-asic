import json
from pathlib import Path
import sys

import pytest

import native_route_trace
sys.modules['native_route_trace_base'] = native_route_trace
from wire600_selective_instrument import instrument as selective
from official_openroad_runtime import instrument
import physical_runtime as runtime
import wire600_selective_plan as source

SCRIPT = Path(__file__).parent/'fixtures/native_rsz_timing_postgrt.tcl'


def enable_native(tmp_path, monkeypatch):
    marker = tmp_path/'marker'
    marker.write_text('3.1.0.dev3\n')
    monkeypatch.setattr(runtime, 'MARKER', marker)
    monkeypatch.setenv('TRIPWIRE_NATIVE_RUNTIME', '1')


def test_default_docker_behavior_unchanged(monkeypatch):
    monkeypatch.delenv('TRIPWIRE_NATIVE_RUNTIME', raising=False)
    assert runtime.container_flags() == ['--docker-no-tty', '--dockerized']


def test_native_flag_without_reviewed_marker_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, 'MARKER', tmp_path/'absent')
    monkeypatch.setenv('TRIPWIRE_NATIVE_RUNTIME', '1')
    with pytest.raises(ValueError, match='reviewed container'):
        runtime.container_flags()


def test_native_backend_avoids_nested_docker_and_binds_target(tmp_path, monkeypatch):
    enable_native(tmp_path, monkeypatch)
    monkeypatch.setenv('TRIPWIRE_SELECTIVE_TARGETS', '')
    assert runtime.container_flags() == []
    target = tmp_path/'wire600_selective_targets.tcl'
    target.write_text('reviewed target fixture')
    runtime.prepare_image('tripwire-wire600-selective:local', tmp_path/'Dockerfile.openroad-wire600-selective')
    assert Path(runtime.os.environ['TRIPWIRE_SELECTIVE_TARGETS']) == target
    with pytest.raises(ValueError, match='Unreviewed'):
        runtime.prepare_image('other', tmp_path/'Dockerfile.other')


def test_native_instrumentation_is_identical_to_passing_backend():
    original = SCRIPT.read_text()
    assert instrument(original, 'tripwire-native-incremental-route:local') == native_route_trace.instrument(original, incremental=True)


def test_selective_instrumentation_only_changes_target_source_path(tmp_path):
    target = tmp_path/'targets.tcl'
    target.write_text('fixture')
    original = SCRIPT.read_text()
    expected = selective(original).replace(
        'source /usr/local/share/tripwire/wire600_selective_targets.tcl',
        'source {'+str(target)+'}')
    assert instrument(original, 'tripwire-wire600-selective:local', target) == expected
    with pytest.raises(ValueError, match='target'):
        instrument(original, 'tripwire-wire600-selective:local')
    with pytest.raises(ValueError, match='Unsafe'):
        selective(original, '/tmp/bad;command')


def test_semantic_config_binding_does_not_relax_values(tmp_path, monkeypatch):
    config = source.BINDING['files']['config']
    monkeypatch.setattr(source, 'BINDING', dict(files={'config': config}))
    reference = Path(__file__).parent/'fixtures/wire600_selective/native_config.json'
    data = json.loads(reference.read_text())
    path = tmp_path/config['path']
    path.parent.mkdir()
    path.write_text(json.dumps(dict(reversed(list(data.items())))))
    monkeypatch.delenv('TRIPWIRE_NATIVE_RUNTIME', raising=False)
    with pytest.raises(ValueError, match='Wrong selective'):
        source.validate_files(tmp_path)
    enable_native(tmp_path, monkeypatch)
    source.validate_files(tmp_path)
    data['CLOCK_PERIOD'] = 21
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='semantic'):
        source.validate_files(tmp_path)
