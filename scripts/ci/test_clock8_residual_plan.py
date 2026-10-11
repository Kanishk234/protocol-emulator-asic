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


@pytest.mark.parametrize('kind', ['antenna', 'hold'])
@pytest.mark.parametrize('mutation', ['source', 'layout', 'delete', 'invert', 'rewire', 'proposal'])
def test_no_unreviewed_change(monkeypatch, kind, mutation):
    before, layout, after, proposal = fixture(monkeypatch, kind)
    if mutation == 'source': before += '\n// altered source'
    if mutation == 'layout': layout += '\n// altered layout'
    if mutation == 'delete': after = after[:after.rfind('\n')]
    if mutation == 'invert': after = after.replace(proposal['buffer_master']+' tripwire', 'sg13cmos5l_inv_4 tripwire')
    if mutation == 'rewire': after = after.replace('.CLK(clk)', '.CLK(other)') if kind == 'hold' else after.replace('.B(b)', '.B(other)')
    if mutation == 'proposal': proposal = copy.deepcopy(proposal);proposal['groups'][0]['sinks'].pop()
    with pytest.raises(ValueError): repair.validate_change(before, layout, after, proposal)


@pytest.mark.parametrize('kind', ['antenna', 'hold'])
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
