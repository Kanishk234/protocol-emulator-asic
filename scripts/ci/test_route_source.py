import copy
import hashlib
import json
from pathlib import Path
import pytest
from route_source import CANDIDATE, REQUIRED, SOURCES, validate_identity, validate_run, validate_saved


def identity(root):
    files = {}
    for name in REQUIRED | {'macro/RM_IHPSG13_1P_512x16_c2_bm_bist/README.md'}:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'candidate': CANDIDATE, 'variant': 'bs-resync', 'source_run_id': 37504886226, 'files': files}


@pytest.mark.parametrize('failure', [None, 'changed', 'missing', 'missing-entry', 'wrong-variant',
                                    'wrong-candidate', 'traversal', 'absolute', 'digest', 'bool-id', 'missing-macro'])
def test_source_identity_refuses_mismatch_and_untrusted_paths(tmp_path, failure):
    data = identity(tmp_path)
    if failure == 'changed':
        (tmp_path / 'src/trw_pin_bs.v').write_text('another RTL trial')
    elif failure == 'missing':
        (tmp_path / 'src/trw_pin_bs.v').unlink()
    elif failure == 'missing-macro':
        (tmp_path / 'macro/RM_IHPSG13_1P_512x16_c2_bm_bist/README.md').unlink()
    elif failure == 'missing-entry':
        del data['files']['src/trw_pin_bs.v']
    elif failure == 'wrong-variant':
        data['variant'] = 'sram'
    elif failure == 'wrong-candidate':
        data['candidate'] = 'wrong'
    elif failure in ('traversal', 'absolute'):
        data['files']['src/../../escaped' if failure == 'traversal' else '/tmp/escaped'] = '0' * 64
    elif failure == 'digest':
        data['files']['src/trw_pin_bs.v'] = 'not a sha256'
    elif failure == 'bool-id':
        data['source_run_id'] = True
    if failure:
        with pytest.raises(ValueError):
            validate_identity(data, tmp_path, 'bs-resync')
    else:
        assert validate_identity(data, tmp_path, 'bs-resync') == data


@pytest.mark.parametrize('failure', [None, 'branch', 'workflow', 'run-id', 'failure', 'unknown'])
@pytest.mark.parametrize('variant', ['bs-resync', 'bs-event-late', 'bs-load-flat', 'bs-event-drop-qual'])
def test_only_successful_main_source_workflow_is_accepted(failure, variant):
    run = {'id': 37504886226, 'head_branch': 'main', 'conclusion': 'success',
           'path': '.github/workflows/gds-drop-counter-screen.yaml'}
    if failure == 'branch':
        run['head_branch'] = 'other-branch'
    elif failure == 'workflow':
        run['path'] = '.github/workflows/other.yaml'
    elif failure == 'run-id':
        run['id'] = 1
    elif failure == 'failure':
        run['conclusion'] = 'failure'
    if failure:
        with pytest.raises(ValueError):
            validate_run(run, 'unknown' if failure == 'unknown' else variant, 37504886226)
    else:
        validate_run(run, variant, 37504886226)


def test_downstream_rechecks_modified_source_and_legacy_artifacts_still_work(tmp_path):
    assert validate_saved(tmp_path) is None
    data = identity(tmp_path)
    path = tmp_path / 'runs/placement-route/source_identity.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data))
    assert validate_saved(tmp_path) == data
    (tmp_path / 'src/trw_pin_bs.v').write_text('tampered after route')
    with pytest.raises(ValueError, match='Source mismatch'):
        validate_saved(tmp_path)


def test_route_artifact_contains_macro_files_needed_by_downstream_identity():
    import yaml
    workflow = yaml.safe_load((Path(__file__).resolve().parents[2] /
                               '.github/workflows/gds-placement-route.yaml').read_text())
    upload = [s for s in workflow['jobs']['harden']['steps']
              if s.get('uses', '').startswith('actions/upload-artifact@')]
    assert len(upload) == 1
    paths = upload[0]['with']['path'].splitlines()
    assert 'macro/**' in paths and 'src/**' in paths and 'runs/placement-route/**' in paths


@pytest.mark.parametrize('variant', ['bs-resync', 'bs-event-late', 'bs-load-flat', 'bs-event-drop-qual'])
def test_route_prepares_exact_named_patch_before_fingerprinting(tmp_path, monkeypatch, variant):
    import route_source
    data = identity(tmp_path)
    applied = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(route_source, 'apply_trial', lambda name, helpers: applied.append(name))
    monkeypatch.setattr(route_source.subprocess, 'check_output',
                        lambda *args, **kwargs: '\0'.join(data['files']).encode())
    prepared = route_source.prepare(variant, 123, Path('helpers'))
    assert applied == [variant]
    assert prepared['variant'] == variant and prepared['source_run_id'] == 123
    assert prepared['files'] == data['files']

@pytest.mark.parametrize('changed', [None, 'src/trw_pin_bs.v', 'src/trw_chan_port.v'])
def test_combination_binds_both_modified_modules(tmp_path, changed):
    data = identity(tmp_path)
    data['variant'] = 'bs-event-drop-qual'
    if changed:
        (tmp_path / changed).write_text('different combined RTL')
        with pytest.raises(ValueError, match='Source mismatch'):
            validate_identity(data, tmp_path, 'bs-event-drop-qual')
    else:
        assert validate_identity(data, tmp_path, 'bs-event-drop-qual') == data
