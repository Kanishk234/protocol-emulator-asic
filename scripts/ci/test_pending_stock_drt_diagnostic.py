import ast
import copy
import json
from pathlib import Path
import sys
import types

import pytest
import yaml

import pending_stock_drt_diagnostic as diag
import test_official_dev4_cpad_route as original_fixture


def row():
    return dict(qualified=False, failures=sorted(diag.ALLOWED_FAILURES),
                final_global_overflow=0, minimum_fast_hold_ns=.05,
                detailed_routing_performed=False, official_gds_signoff=False)


def test_only_the_specific_initial_antenna_failure_is_admitted():
    assert diag.admitted_screen(row())
    for field, value in [('qualified', True), ('final_global_overflow', 1),
                         ('minimum_fast_hold_ns', 0), ('detailed_routing_performed', True)]:
        bad = row(); bad[field] = value
        assert not diag.admitted_screen(bad)
    for failures in [[], ['antenna__violating__nets: 2', 'antenna__violating__pins: 2'],
                     sorted(diag.ALLOWED_FAILURES) + ['electrical violation']]:
        bad = row(); bad['failures'] = failures
        assert not diag.admitted_screen(bad)


def source(tmp_path, monkeypatch):
    monkeypatch.setattr(original_fixture, 'route', diag)
    path = original_fixture.make_source(tmp_path, monkeypatch)
    run_path = tmp_path / 'official-dev4-source-run.json'
    run = json.loads(run_path.read_text()); run['conclusion'] = 'failure'
    run_path.write_text(json.dumps(run))
    q = row(); q['source_state'] = str(path)
    (tmp_path / 'runs/stock-corner-audit/screen_qualification.json').write_text(json.dumps(q))
    monkeypatch.setitem(sys.modules, 'stock_screen_gate', types.SimpleNamespace(qualify=lambda *args: q))
    monkeypatch.setenv('DIAGNOSTIC_DRT_APPROVAL', str(diag.SOURCE_RUN))
    return path


def test_exact_source_and_explicit_approval_are_required(tmp_path, monkeypatch):
    path = source(tmp_path, monkeypatch)
    assert diag.verify_source()[0].resolve() == path.resolve()
    monkeypatch.delenv('DIAGNOSTIC_DRT_APPROVAL')
    with pytest.raises(ValueError, match='approval'):
        diag.verify_source()


def test_other_source_is_rejected(tmp_path, monkeypatch):
    source(tmp_path, monkeypatch)
    p = tmp_path / 'official-dev4-source-run.json'
    run = json.loads(p.read_text()); run['id'] += 1; p.write_text(json.dumps(run))
    with pytest.raises(ValueError, match='exact diagnostic source'):
        diag.verify_source()


def test_timing_is_not_waived():
    comparison = {'corners': {c: {p: {f'timing__setup__ws__corner:{c}': 0,
                                      f'timing__hold__ws__corner:{c}': .1}
                                  for p in ('before', 'after')} for c in diag.CORNERS}}
    assert diag.admitted_timing(comparison)
    for kind, value in [('setup', -.001), ('hold', .049), ('setup', float('nan'))]:
        bad = copy.deepcopy(comparison)
        bad['corners'][diag.CORNERS[0]]['before'][f'timing__{kind}__ws__corner:{diag.CORNERS[0]}'] = value
        assert not diag.admitted_timing(bad)


def test_final_extracted_gate_logic_is_unchanged():
    root = Path(__file__).parent
    def gates(name):
        function = next(n for n in ast.parse((root / name).read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'extract')
        start = next(i for i, n in enumerate(function.body) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'failures' for t in n.targets))
        end = next(i for i, n in enumerate(function.body) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'result' for t in n.targets))
        return [ast.dump(n) for n in function.body[start:end]]
    assert gates('official_dev4_cpad_route.py') == gates('pending_stock_drt_diagnostic.py')


def test_push_cannot_start_the_diagnostic_and_jobs_keep_pdk_root():
    p = Path(__file__).parents[2] / '.github/workflows/gds-pending-stock-drt-diagnostic.yaml'
    w = yaml.safe_load(p.read_text())
    assert w['on']['workflow_dispatch']['inputs']['approved_diagnostic']['default'] is False
    assert "github.event_name == 'workflow_dispatch'" in w['jobs']['route']['if']
    assert 'inputs.approved_diagnostic' in w['jobs']['route']['if']
    for job in w['jobs'].values():
        assert job['env']['PDK_ROOT'] == '/home/runner/pdk'
        assert job['env']['DIAGNOSTIC_DRT_APPROVAL'] == str(diag.SOURCE_RUN)
