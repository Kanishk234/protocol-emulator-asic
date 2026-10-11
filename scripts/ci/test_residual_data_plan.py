import hashlib
import pytest
import residual_data_plan as runner
from event_nor2_screen import logical_cells


def fixture(monkeypatch):
    nl = 'sg13cmos5l_nand3_1 _28807_ (.A(a), .B(b), .C(c), .Y(_03831_));\n'
    layout = ''
    for i in range(16):
        master = 'sg13cmos5l_antennanp' if i < 8 else 'sg13cmos5l_inv_1'
        pins = '.A(_03831_)' + ('' if i < 8 else f', .Y(out{i})')
        nl += f'{master} sink{i} ({pins});\n'
        layout += f'- sink{i} {master} + PLACED ( {i*100} 200 ) N ;\n'
    monkeypatch.setattr(runner, 'NL_SHA', hashlib.sha256(nl.encode()).hexdigest())
    monkeypatch.setattr(runner, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    return nl, layout


def test_actual_target_shape_preserves_thirteen_loads_six_diodes(monkeypatch):
    nl = 'sg13cmos5l_nor2_1 _28820_ (.A(a), .B(b), .Y(_03844_));\n'
    layout = ''
    for i in range(13):
        master = 'sg13cmos5l_antennanp' if i < 6 else 'sg13cmos5l_inv_1'
        pins = '.A(_03844_)' + ('' if i < 6 else f', .Y(out{i})')
        nl += f'{master} sink{i} ({pins});\n'
        layout += f'- sink{i} {master} + PLACED ( {i*100} 200 ) N ;\n'
    monkeypatch.setattr(runner, 'NL_SHA', hashlib.sha256(nl.encode()).hexdigest())
    monkeypatch.setattr(runner, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    p = runner.plan(nl, layout, '_28820_')
    assert [len(g['sinks']) for g in p['groups']] == [4, 4, 4, 1]
    runner.validate_change(nl, layout, changed(nl, p), p)
    after = changed(nl, p).replace('sg13cmos5l_antennanp sink0', 'sg13cmos5l_inv_1 sink0')
    with pytest.raises(ValueError): runner.validate_change(nl, layout, after, p)


def changed(nl, proposal):
    cells = logical_cells(nl)
    for g in proposal['groups']:
        for n, pin in g['sinks']:
            m, pins = cells[n]
            cells[n] = (m, tuple((p, g['net'] if p == pin else v) for p, v in pins))
        cells[g['buffer']] = ('sg13cmos5l_buf_4', [('A', g['source_net']), ('X', g['net'])])
    return '\n'.join(m+' '+n+' ('+', '.join('.'+p+'('+v+')' for p, v in pins)+');'
                     for n, (m, pins) in cells.items())


def test_complete_partition_conserves_logic_and_diodes(monkeypatch):
    nl, layout = fixture(monkeypatch)
    p = runner.plan(nl, layout, '_28807_')
    assert [len(g['sinks']) for g in p['groups']] == [4]*4
    assert len({tuple(s) for g in p['groups'] for s in g['sinks']}) == 16
    runner.validate_change(nl, layout, changed(nl, p), p)
    import json
    runner.validate_change(nl, layout, changed(nl, p), json.loads(json.dumps(p)))
    assert not p['physical_timing_measured'] and not p['legal_site_verified']


def test_binding_supplies_complete_preflight_and_no_clock_or_constraint_command(monkeypatch):
    nl, layout = fixture(monkeypatch)
    call = runner.target_call(nl, layout, '_28807_')
    assert call.startswith('tripwire_clock8_residual sg13cmos5l_buf_4 ')
    for i in range(16):
        assert call.count(f'sink{i}/A') == 1
        assert call.count('{sink'+str(i)+' A}') == 1
    assert call.count('tripwire_residual_data__28807_') == 8
    assert 'set_clock' not in call and 'remove_cell' not in call


def test_generated_call_is_valid_tcl_and_covers_every_sink(monkeypatch, tmp_path):
    import subprocess
    nl, layout = fixture(monkeypatch)
    script = r'''
proc tripwire_clock8_residual {master expectations groups} {
    if {$master ne "sg13cmos5l_buf_4" || [llength $expectations] != 1 || [llength $groups] != 4} {error "Bad envelope"}
    lassign [lindex $expectations 0] net pins masters
    if {[llength $pins] != 17 || [llength $masters] != 17} {error "Incomplete preflight"}
    set seen {}
    foreach g $groups {
        if {[llength $g] != 6} {error "Bad group"}
        lassign $g name downstream source rail location sinks
        if {$source ne $net || $rail ne "_28807_" || [llength $location] != 2 || [llength $sinks] != 4} {error "Bad partition"}
        foreach s $sinks {
            if {[llength $s] != 2 || $s in $seen} {error "Duplicate/invalid sink"}
            lappend seen $s
        }
    }
    if {[llength $seen] != 16} {error "Lost sink"}
    puts complete
}
'''
    path = tmp_path/'binding.tcl'
    path.write_text(script+runner.target_call(nl, layout, '_28807_'))
    result = subprocess.run(['tclsh', str(path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert 'complete' in result.stdout.splitlines()


@pytest.mark.parametrize('failure', ['source', 'layout', 'diode', 'master', 'rewire', 'proposal'])
def test_rejects_stale_source_or_unintended_change(monkeypatch, failure):
    nl, layout = fixture(monkeypatch)
    p = runner.plan(nl, layout, '_28807_')
    after = changed(nl, p)
    if failure == 'source': nl += 'changed'
    if failure == 'layout': layout += 'changed'
    if failure == 'diode': after = after.replace('sg13cmos5l_antennanp sink0', 'sg13cmos5l_inv_1 sink0')
    if failure == 'master': after = after.replace('sg13cmos5l_nand3_1', 'sg13cmos5l_nand2_1')
    if failure == 'rewire': after = after.replace('.A(a)', '.A(other)')
    if failure == 'proposal': p['groups'][0]['sinks'].pop()
    with pytest.raises(ValueError): runner.validate_change(nl, layout, after, p)
