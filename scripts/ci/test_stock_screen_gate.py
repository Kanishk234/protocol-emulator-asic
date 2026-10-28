import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from postgrt_timing import CORNERS
from stock_screen_gate import qualify


def fixture(root, *, fast=0.05, setup=0, electrical=0, antenna=0, overflow=0):
    physical, audit = root / 'physical', root / 'audit'
    final = physical / '44-openroad-resizertimingpostgrt'
    final.mkdir(parents=True)
    state = {}
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        path = final / ('chip.' + key)
        path.write_text('source ' + key)
        state[key] = str(path)
    source = physical / '45-openroad-stamidpnr-3/state_out.json'
    source.parent.mkdir()
    source.write_text(json.dumps(state))
    paths = [source] + [type(source)(path) for path in state.values()]
    receipt = dict(source_state=str(source), unchanged_physical_view_hashes={
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}, fresh_corner_metrics={})
    for corner in CORNERS:
        row = {f'timing__setup__ws__corner:{corner}': setup,
               f'timing__hold__ws__corner:{corner}': fast if corner == CORNERS[0] else 0.1}
        row.update({f'design__max_{kind}_violation__count__corner:{corner}': electrical
                    for kind in ('slew', 'cap', 'fanout')})
        receipt['fresh_corner_metrics'][corner] = row
        for stage in ('before-', 'after-'):
            path = audit / (stage + corner) / '1-openroad-stamidpnr/or_metrics_out.json'
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(row))
    receipt['fresh_antenna_metrics'] = {key: antenna for key in (
        'antenna__violating__nets', 'antenna__violating__pins')}
    path = audit / 'fresh-antenna/1-openroad-checkantennas/or_metrics_out.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(receipt['fresh_antenna_metrics']))
    (audit / 'read_only_audit.json').write_text(json.dumps(receipt))
    # Earlier zero must not hide the final overflow.
    (final / 'openroad-resizertimingpostgrt.log').write_text(
        f'Total 100 80 80.00% 0 / 0 / 0\nTotal 100 80 80.00% 1 / 0 / {overflow}\n')
    return physical, audit


def test_exact_acceptance_boundary_passes(tmp_path):
    result = qualify(*fixture(tmp_path))
    assert result['qualified'] and not result['official_gds_signoff']


@pytest.mark.parametrize('change', [dict(fast=0.049999), dict(setup=-0.00001),
                                   dict(electrical=1), dict(antenna=1), dict(overflow=1)])
def test_every_existing_gate_enforced(tmp_path, change):
    result = qualify(*fixture(tmp_path, **change))
    assert not result['qualified'] and result['failures']


def test_changed_source_view_rejected(tmp_path):
    physical, audit = fixture(tmp_path)
    (physical / '44-openroad-resizertimingpostgrt/chip.odb').write_text('changed')
    with pytest.raises(ValueError, match='source changed'):
        qualify(physical, audit)


def test_missing_corner_rejected(tmp_path):
    physical, audit = fixture(tmp_path)
    path = audit / 'read_only_audit.json'
    data = json.loads(path.read_text())
    del data['fresh_corner_metrics'][CORNERS[1]]
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='audit corner'):
        qualify(physical, audit)


def test_stale_or_modified_raw_metrics_rejected(tmp_path):
    physical, audit = fixture(tmp_path)
    path = audit / ('after-' + CORNERS[0]) / '1-openroad-stamidpnr/or_metrics_out.json'
    data = json.loads(path.read_text())
    data[f'timing__hold__ws__corner:{CORNERS[0]}'] = -1
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='raw timing'):
        qualify(physical, audit)


@pytest.mark.parametrize('value', [True, -1, 0.0, float('nan')])
def test_invalid_violation_count_rejected(tmp_path, value):
    physical, audit = fixture(tmp_path, electrical=value)
    with pytest.raises(ValueError):
        qualify(physical, audit)


def test_missing_final_overflow_report_rejected(tmp_path):
    physical, audit = fixture(tmp_path)
    (physical / '44-openroad-resizertimingpostgrt/openroad-resizertimingpostgrt.log').write_text('no totals')
    with pytest.raises(ValueError, match='overflow report'):
        qualify(physical, audit)


def test_forged_zero_antenna_receipt_rejected(tmp_path):
    physical, audit = fixture(tmp_path)
    path = audit / 'fresh-antenna/1-openroad-checkantennas/or_metrics_out.json'
    path.write_text(json.dumps({'antenna__violating__nets': 2, 'antenna__violating__pins': 2}))
    with pytest.raises(ValueError, match='raw antenna'):
        qualify(physical, audit)


@pytest.mark.parametrize('antenna,expected_code', [(0, 0), (1, 1)])
def test_cli_status_matches_qualification_and_saves_report(tmp_path, antenna, expected_code):
    physical, audit = fixture(tmp_path, antenna=antenna)
    script = Path(__file__).with_name('stock_screen_gate.py')
    result = subprocess.run([sys.executable, str(script.resolve()), '--physical', str(physical),
                             '--audit', str(audit)], capture_output=True, text=True)
    assert result.returncode == expected_code, result.stderr
    report = json.loads((audit / 'screen_qualification.json').read_text())
    assert report['qualified'] is (expected_code == 0)
