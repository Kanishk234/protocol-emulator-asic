import copy
import hashlib
import pytest
import clock8_residual_plan as repair
from event_nor2_screen import logical_cells


def fixture(monkeypatch, kind):
    if kind == 'antenna':
        rows = ['sg13cmos5l_nand2_1 _29457_ (.A(a), .B(b), .Y(_04467_));']
        rows += [f'sg13cmos5l_antennanp ANTENNA_{i} (.A(_04467_));' for i in range(12)]
        rows += [f'sg13cmos5l_buf_1 sink{i} (.A(_04467_), .X(out{i}));' for i in range(8)]
    elif kind == 'clock':
        rows = []
        for branch in range(4):
            rows.append(f'sg13cmos5l_buf_8 clkbuf_2_{branch}_0_clk_regs (.A(root), .X(clock{branch}));')
            rows += [f'sg13cmos5l_buf_8 leaf{branch}_{i} (.A(clock{branch}), .X(leafnet{branch}_{i}));' for i in range(16)]
    else:
        rows = []
        for endpoint, net, driver, master in repair.HOLD:
            rows += [f'{master} {driver} (.A(a), .Y({net}));',
                     f'sg13cmos5l_dfrbpq_1 {endpoint} (.D({net}), .CLK(clk), .Q(q{endpoint}));']
    before = '\n'.join(rows)
    cells = logical_cells(before)
    layout = '\n'.join(f'- {n} {m} + PLACED ( {i*100} {i*30} ) N ;' for i, (n, (m, p)) in enumerate(cells.items()))
    monkeypatch.setattr(repair, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    monkeypatch.setattr(repair, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    proposal = repair.plan(before, layout, kind)
    rewires = {(n, p):g['net'] for g in proposal['groups'] for n, p in g['sinks']}
    after = []
    for n, (m, pins) in cells.items():
        ports = ', '.join(f'.{p}({rewires.get((n,p),v)})' for p,v in pins)
        after.append(f'{m} {n} ({ports});')
    for g in proposal['groups']:
        after.append(f"{proposal['buffer_master']} {g['buffer']} (.A({g['source_net']}), .X({g['net']}));")
    return before, layout, '\n'.join(after), proposal


@pytest.mark.parametrize('kind', ['antenna', 'hold'])
def test_exact_identity_repair(monkeypatch, kind):
    before, layout, after, proposal = fixture(monkeypatch, kind)
    result = repair.validate_change(before, layout, after, proposal)
    assert result['added_buffers'] == 2
    assert result['downstream_sink_pins'] == ([7,7] if kind == 'antenna' else [1,1])
    assert result['upstream_sink_pins'] == (8 if kind == 'antenna' else 1)
    assert not result['physical_timing_measured']


@pytest.mark.parametrize('kind', ['antenna', 'hold', 'clock'])
@pytest.mark.parametrize('mutation', ['source', 'layout', 'delete', 'invert', 'rewire', 'proposal'])
def test_no_unreviewed_change(monkeypatch, kind, mutation):
    before, layout, after, proposal = fixture(monkeypatch, kind)
    if mutation == 'source': before += '\n// altered source'
    if mutation == 'layout': layout += '\n// altered layout'
    if mutation == 'delete': after = after[:after.rfind('\n')]
    if mutation == 'invert': after = after.replace(proposal['buffer_master']+' tripwire', 'sg13cmos5l_inv_4 tripwire')
    if mutation == 'rewire':
        old, new = {'hold': ('.CLK(clk)', '.CLK(other)'),
                    'antenna': ('.B(b)', '.B(other)'),
                    'clock': ('.A(root)', '.A(other)')}[kind]
        after = after.replace(old, new)
    if mutation == 'proposal': proposal = copy.deepcopy(proposal);proposal['groups'][0]['sinks'].pop()
    with pytest.raises(ValueError): repair.validate_change(before, layout, after, proposal)


@pytest.mark.parametrize('kind', ['antenna', 'hold', 'clock'])
def test_generated_tcl_is_complete_and_bounded(monkeypatch, kind, tmp_path):
    import subprocess
    from pathlib import Path
    before, layout, after, proposal = fixture(monkeypatch, kind)
    call = repair.target_call(before, layout, kind)
    assert call.count('tripwire_clock8_residual ') == 1
    assert 'exec ' not in call
    target = tmp_path / 'targets.tcl'
    target.write_text(call)
    binding = Path(__file__).with_name('clock8_residual.tcl').resolve()
    script = f'source {{{binding}}}\nset f [open {{{target}}}]\nset text [read $f]\nclose $f\nif {{![info complete $text]}} {{exit 1}}\nputs complete\n'
    check = tmp_path / 'check.tcl'
    check.write_text(script)
    result = subprocess.run(['tclsh', str(check)], text=True, capture_output=True)
    assert result.returncode == 0 and 'complete' in result.stdout.splitlines()
    assert not result.stderr


def fanout_fixture(monkeypatch):
    rows = []
    for i in range(30):
        net = f'net{i}'
        rows.append(f'sg13cmos5l_nand2_1 driver{i} (.A(a), .B(b), .Y({net}));')
        for j in range(20 if i == 0 else 9):
            master = 'sg13cmos5l_antennanp' if j >= 8 else 'sg13cmos5l_buf_1'
            rows.append(f'{master} sink{i}_{j} (.A({net}));')
    before = '\n'.join(rows)
    cells = logical_cells(before)
    layout = '\n'.join(f'- {n} {m} + PLACED ( {i*100} {i*30} ) N ;' for i,(n,(m,p)) in enumerate(cells.items()))
    monkeypatch.setattr(repair, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    monkeypatch.setattr(repair, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    return before, layout


def test_fanout_policy_reserves_loads_and_preserves_diodes(monkeypatch):
    before, layout = fanout_fixture(monkeypatch)
    proposal = repair.plan(before, layout, 'fanout')
    assert proposal['added_buffers'] == 32
    assert max(proposal['downstream_sink_pins']) <= 6
    cells = logical_cells(before)
    moved = {(n,p):g['net'] for g in proposal['groups'] for n,p in g['sinks']}
    rows = []
    for n,(m,pins) in cells.items():
        ports = ', '.join(f'.{p}({moved.get((n,p),v)})' for p,v in pins)
        rows.append(f'{m} {n} ({ports});')
    for g in proposal['groups']:
        rows.append(f"{proposal['buffer_master']} {g['buffer']} (.A({g['source_net']}), .X({g['net']}));")
    after = '\n'.join(rows)
    repair.validate_change(before, layout, after, proposal)
    nets = {}
    for n,(m,pins) in logical_cells(after).items():
        for p,v in pins: nets.setdefault(v,[]).append((n,p))
    for i in range(30):
        assert len(nets[f'net{i}'])-1 <= 6
    assert repair.target_call(before, layout, 'fanout').count('tripwire_clock8_residual ') == 1
    with pytest.raises(ValueError):
        repair.validate_change(before, layout, after.replace('sg13cmos5l_antennanp sink0_8', 'sg13cmos5l_buf_1 sink0_8'), proposal)


def test_data_fanout_targets_preserve_observed_bracket_encoding(monkeypatch):
    before, layout = fanout_fixture(monkeypatch)
    before = before.replace('net0)', '\\u_chip.g_unit[0].r[1] )')
    monkeypatch.setattr(repair, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    call = repair.target_call(before, layout, 'fanout')
    assert '{u_chip.g_unit\\[0\\].r\\[1\\]}' in call
    assert '{u_chip.g_unit[0].r[1]}' not in call


def test_clock_branch_identity_and_bounds(monkeypatch):
    before, layout, after, proposal = fixture(monkeypatch, 'clock')
    repair.validate_change(before, layout, after, proposal)
    assert proposal['added_buffers'] == 8
    assert proposal['buffer_master'] == 'sg13cmos5l_buf_8'
    assert proposal['upstream_sink_pins'] == 2
    assert proposal['downstream_sink_pins'] == [8]*8
    for mutation in (after.replace('.A(clock0)', '.A(wrong)'),
                     after.replace('sg13cmos5l_buf_8 tripwire', 'sg13cmos5l_inv_8 tripwire')):
        with pytest.raises(ValueError):
            repair.validate_change(before, layout, mutation, proposal)


def test_clock_branch_rejects_unreviewed_sink(monkeypatch):
    before, layout, after, proposal = fixture(monkeypatch, 'clock')
    before = before.replace('leaf0_0 (.A(clock0)', 'leaf0_0 (.CLK(clock0)')
    monkeypatch.setattr(repair, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    with pytest.raises(ValueError, match='clock buffer loads'):
        repair.plan(before, layout, 'clock')


@pytest.mark.parametrize('mutation', ['driver_master', 'load_master', 'placement', 'load_count'])
def test_clock_branch_source_guard(monkeypatch, mutation):
    before, layout, after, proposal = fixture(monkeypatch, 'clock')
    if mutation == 'driver_master':
        before = before.replace('sg13cmos5l_buf_8 clkbuf_2_0', 'sg13cmos5l_buf_4 clkbuf_2_0')
    elif mutation == 'load_master':
        before = before.replace('sg13cmos5l_buf_8 leaf0_0 ', 'sg13cmos5l_buf_4 leaf0_0 ')
    elif mutation == 'placement':
        layout = '\n'.join(line for line in layout.splitlines() if not line.startswith('- leaf0_0 '))
    else:
        before = '\n'.join(line for line in before.splitlines() if ' leaf0_0 ' not in line)
    monkeypatch.setattr(repair, 'NL_SHA', hashlib.sha256(before.encode()).hexdigest())
    monkeypatch.setattr(repair, 'DEF_SHA', hashlib.sha256(layout.encode()).hexdigest())
    with pytest.raises(ValueError):
        repair.plan(before, layout, 'clock')
