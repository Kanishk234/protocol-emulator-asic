"""Reject ECOs that delete antenna protection or alter the buffered function."""
import hashlib
import pytest
import antenna_branch as branch


def fixture(monkeypatch):
    rows = ['sg13cmos5l_nand3_1 _28807_ (.A(a), .B(b), .C(c), .Y(_03831_));']
    rows += [f'sg13cmos5l_antennanp ANTENNA_{i} (.A(_03831_));' for i in range(1, 8)]
    rows += [f'sg13cmos5l_nor2_1 {n} (.A(a), .B(_03831_), .Y(out{n}));'
             for n in ['_28936_', '_28973_', '_29032_', '_29046_', '_29087_']]
    rows += ['sg13cmos5l_mux4_1 _28812_ (.S1(_03831_), .X(m));',
             'sg13cmos5l_a22oi_1 _44662_ (.A1(_03831_), .Y(n));',
             'sg13cmos5l_buf_1 place7617 (.A(_03831_), .X(o));']
    before = '\n'.join(rows)
    monkeypatch.setattr(branch, 'STRENGTH_NETLIST_SHA', hashlib.sha256(before.encode()).hexdigest())
    from event_nor2_screen import logical_cells
    after = []
    for name, (master, pins) in logical_cells(before).items():
        ports = ', '.join(f'.{pin}({branch.NEW_NET if (name, pin) in branch.SINKS else net})'
                          for pin, net in pins)
        after.append(f'{master} {name} ({ports});')
    after.append(f'sg13cmos5l_buf_4 {branch.BUFFER} (.A({branch.SOURCE_NET}), .X({branch.NEW_NET}));')
    return before, '\n'.join(after)


def test_identity_partition_preserves_all_cells(monkeypatch):
    before, after = fixture(monkeypatch)
    result = branch.validate_change(before, after)
    assert result['upstream_sink_pins'] == result['downstream_sink_pins'] == 8
    assert result['retained_antenna_cells'] is True
    assert result['topology_only'] is True


def test_promote_checks_branch_identity_before_using_new_views(tmp_path, monkeypatch):
    import json
    from sram_relocate_screen import promote
    before, after = fixture(monkeypatch)
    baseline = tmp_path / 'original.v'
    baseline.write_text(before)
    odb = tmp_path / 'chip.odb'
    odb.with_suffix('.baseline.nl.v').write_text(before)
    odb.with_suffix('.eco.nl.v').write_text(after)
    odb.with_suffix('.eco.pnl.v').write_text(after)
    state = tmp_path / 'state_out.json'
    state.write_text(json.dumps(dict(odb=str(odb), spef='old')))
    result = json.loads(promote(state, baseline, 'antenna-branch').read_text())
    assert result['spef'] is None
    odb.with_suffix('.eco.nl.v').write_text(after.replace('sg13cmos5l_buf_4', 'sg13cmos5l_inv_4'))
    with pytest.raises(ValueError): promote(state, baseline, 'antenna-branch')


def test_manual_screen_pins_original_route_and_is_bounded():
    from pathlib import Path
    import yaml
    path = Path(__file__).resolve().parents[2] / '.github/workflows/gds-antenna-branch-screen.yaml'
    workflow = yaml.safe_load(path.read_text())
    job = workflow['jobs']['harden']
    download = next(s for s in job['steps'] if 'download-artifact@' in s.get('uses', ''))
    assert download['with']['run-id'] == 37954320974
    assert job['timeout-minutes'] == 120
    trial = next(s for s in job['steps'] if s['name'].startswith('Split one'))
    assert trial['timeout-minutes'] == 95
    assert trial['run'].endswith('--target antenna-branch')


@pytest.mark.parametrize('fault', ['source', 'delete_diode', 'resize', 'invert', 'wrong_input',
                                 'wrong_output', 'extra_cell', 'unrelated_net', 'missed_sink'])
def test_reject_nonidentity_or_unmatched_branch(monkeypatch, fault):
    before, after = fixture(monkeypatch)
    if fault == 'source': before += '\n'
    elif fault == 'delete_diode':
        after = '\n'.join(line for line in after.splitlines() if 'ANTENNA_2 ' not in line)
    elif fault == 'resize': after = after.replace('sg13cmos5l_nand3_1', 'sg13cmos5l_nand3_2')
    elif fault == 'invert': after = after.replace('sg13cmos5l_buf_4', 'sg13cmos5l_inv_4')
    elif fault == 'wrong_input': after = after.replace('.A(_03831_), .X(tripwire_antenna_branch_net)', '.A(a), .X(tripwire_antenna_branch_net)')
    elif fault == 'wrong_output': after = after.replace('.X(tripwire_antenna_branch_net)', '.X(other)')
    elif fault == 'extra_cell': after += '\nsg13cmos5l_buf_1 extra (.A(a), .X(b));'
    elif fault == 'unrelated_net': after = after.replace('.Y(out_28936_)', '.Y(other)')
    else: after = after.replace('ANTENNA_2 (.A(tripwire_antenna_branch_net))', 'ANTENNA_2 (.A(_03831_))')
    with pytest.raises(ValueError): branch.validate_change(before, after)
