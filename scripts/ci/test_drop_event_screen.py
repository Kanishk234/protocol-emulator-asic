import json
from pathlib import Path

import pytest
import yaml

from event_nor2_screen import validate_drop_netlist, promote_netlists

ORIGINAL = ('sg13cmos5l_nor2_2 _27853_ (.A(_21095_), .B(_02509_), .Y(_02510_));\n'
            'sg13cmos5l_nor2_1 _31567_ (.A(_05964_), .B(_05968_), .Y(_05970_));')
CHANGED = ORIGINAL.replace('nor2_1 _31567_', 'nor2_2 _31567_')


def test_only_audited_drop_cell_changes():
    validate_drop_netlist(ORIGINAL, CHANGED)
    for bad in (ORIGINAL, CHANGED.replace('_05968_', 'wrong'),
                CHANGED.replace('nor2_2 _27853_', 'nor2_1 _27853_'),
                CHANGED + '\nsg13cmos5l_inv_1 extra (.A(a), .Y(b));'):
        with pytest.raises(ValueError):
            validate_drop_netlist(ORIGINAL, bad)


def test_fresh_source_and_both_repairs_required(tmp_path):
    source = tmp_path / 'original.v'
    source.write_text(ORIGINAL)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps({'odb': str(tmp_path / 'chip.odb')}))
    (tmp_path / 'chip.baseline.nl.v').write_text(ORIGINAL)
    (tmp_path / 'chip.eco.nl.v').write_text(CHANGED)
    powered = tmp_path / 'chip.eco.pnl.v'
    powered.write_text(CHANGED)
    assert promote_netlists(state, source, drop=True).exists()
    powered.write_text(ORIGINAL)
    with pytest.raises(ValueError, match='Powered netlist missing dropped'):
        promote_netlists(state, source, drop=True)
    powered.write_text(CHANGED)
    (tmp_path / 'chip.baseline.nl.v').write_text(CHANGED)
    with pytest.raises(ValueError, match='source ODB/netlist mismatch'):
        promote_netlists(state, source, drop=True)


def test_workflow_freezes_source_and_changes_one_cell_only():
    root = Path(__file__).parents[2]
    workflow = yaml.safe_load((root / '.github/workflows/gds-drop-event-screen.yaml').read_text())
    job = workflow['jobs']['harden']
    assert job['env']['ECO_PROFILE'] == 'drop-nor2'
    steps = job['steps']
    download = next(s for s in steps if s.get('uses', '').startswith('actions/download-artifact'))
    assert download['with']['run-id'] == 37736921949
    assert download['with']['name'] == 'gds-event-nor2-37736921949'
    docker = (root / 'scripts/ci/Dockerfile.openroad-drop-event').read_text()
    assert 'COPY drop_event_size.tcl' in docker
    assert 'COPY event_nor2_size.tcl' not in docker
    wrapper = (root / 'scripts/ci/openroad_event_nor2_wrapper.sh').read_text()
    assert 'tripwire_size_drop_cell nor2' in wrapper
    assert 'tripwire_size_drop_cell inv' not in wrapper
