import json
from pathlib import Path

import pytest

import native_margin_screen as runner
from postgrt_timing import CORNERS

BEFORE = 'sg13cmos5l_buf_1 data (.A(a), .X(n));\nsg13cmos5l_buf_1 clock (.A(clk), .X(ck));\n'
AFTER = BEFORE + 'sg13cmos5l_antennanp diode (.A(n));\n'


def fixture_states(tmp_path):
    nl = tmp_path/'before.v'; nl.write_text(BEFORE)
    before = tmp_path/'before.json'; before.write_text(json.dumps({'nl': str(nl), 'odb': '/before.odb'}))
    repaired = tmp_path/'repaired.json'
    repaired.write_text(json.dumps({'nl': str(nl), 'pnl': '/stale.pnl', 'odb': '/after.odb',
                                    'spef': '/stale.spef', 'sdf': '/stale.sdf', 'lib': '/stale.lib'}))
    timing = tmp_path/'timing'
    for c in CORNERS:
        stage = timing/f'after-{c}'/'1-openroad-stamidpnr'; stage.mkdir(parents=True)
        (stage/'state_in.json').write_text(json.dumps({'odb': '/after.odb'}))
        (stage/'native_antenna.nl.v').write_text(AFTER)
        (stage/'native_antenna.pnl.v').write_text('powered export')
    return before, repaired, timing


def test_native_antenna_command_keeps_congestion_disallowed(tmp_path):
    source = tmp_path/'state_out.json'
    nested = tmp_path/'1-openroad-diodeinsertion'; nested.mkdir()
    log = nested/'openroad-diodeinsertion.log'
    log.write_text('+ repair_antennas sg13cmos5l_antennanp -iterations 3 -ratio_margin 50\n')
    runner.check_post_antenna_command({'GRT_ALLOW_CONGESTION': False}, source)
    with pytest.raises(ValueError):
        runner.check_post_antenna_command({'GRT_ALLOW_CONGESTION': True}, source)
    log.write_text(log.read_text().rstrip()+' -allow_congestion\n')
    with pytest.raises(ValueError):
        runner.check_post_antenna_command({'GRT_ALLOW_CONGESTION': False}, source)


def test_readback_promotes_actual_new_views_and_discards_stale_parasitics(tmp_path):
    before, repaired, timing = fixture_states(tmp_path)
    state = json.loads(runner.audit_post_antenna(before, repaired, timing).read_text())
    assert Path(state['nl']).read_text() == AFTER
    assert state['pnl'] != '/stale.pnl'
    assert all(state[k] is None for k in ('spef', 'sdf', 'lib'))
    assert state['odb'] == '/after.odb'


@pytest.mark.parametrize('bad', ['clock', 'different_odb', 'missing_export', 'corner_disagreement'])
def test_bad_readback_rejected(tmp_path, bad):
    before, repaired, timing = fixture_states(tmp_path)
    stage = timing/f'after-{CORNERS[0]}'/'1-openroad-stamidpnr'
    if bad == 'clock':
        for c in CORNERS:
            (timing/f'after-{c}'/'1-openroad-stamidpnr/native_antenna.nl.v').write_text(AFTER.replace('.A(clk)', '.A(other)'))
    elif bad == 'different_odb':
        (stage/'state_in.json').write_text(json.dumps({'odb': '/wrong.odb'}))
    elif bad == 'missing_export':
        (stage/'native_antenna.pnl.v').unlink()
    else:
        (stage/'native_antenna.nl.v').write_text(AFTER+'sg13cmos5l_antennanp extra (.A(a));\n')
    with pytest.raises(ValueError):
        runner.audit_post_antenna(before, repaired, timing)


@pytest.mark.parametrize('antenna_count', [0, 2])
def test_main_uses_fresh_postrepair_evidence_and_keeps_antenna_gate(tmp_path, monkeypatch, antenna_count):
    monkeypatch.chdir(tmp_path); monkeypatch.setenv('PDK_ROOT', '/pdk')
    before, repaired, _ = fixture_states(tmp_path)
    root = Path('runs/native-stock-screen'); root.mkdir(parents=True)
    (root/'recipe.json').write_text(json.dumps({'stock_sequence': True}))
    before = root/'before.json'; before.write_text((tmp_path/'before.json').read_text())
    (root/'openroad-resizertimingpostgrt.log').write_text('original overflow checked')
    Path('src').mkdir(); Path('src/config_native_stock.json').write_text('{}')
    monkeypatch.setattr(runner, 'checkpoint', lambda _, final_antenna=False: repaired if final_antenna else before)
    monkeypatch.setattr(runner, 'validate_overflow', lambda _: None)
    monkeypatch.setattr(runner, 'check_post_antenna_command', lambda config, source: None)
    def stock(**kw):
        assert kw['stop_step'] == 'OpenROAD.RepairAntennas-1'
        assert kw['extra_tcl'].name == 'native_post_antenna_audit.tcl'
        output = root/'timing'
        output.mkdir()
        rows = {}
        for c in CORNERS:
            stage = output/f'after-{c}'/'1-openroad-stamidpnr'; stage.mkdir(parents=True)
            (stage/'state_in.json').write_text(json.dumps({'odb': '/after.odb'}))
            (stage/'native_antenna.nl.v').write_text(AFTER)
            (stage/'native_antenna.pnl.v').write_text('powered export')
            (stage/'checks.rpt').write_text('max slew violation count 0\nmax fanout violation count 0\nmax cap violation count 0\n')
            (stage/'electrical_margin.rpt').write_text('measured')
            rows[c] = {'after': {f'timing__setup__ws__corner:{c}': 0, f'timing__hold__ws__corner:{c}': .08}}
        (output/'comparison.json').write_text(json.dumps({'corners': rows}))
    monkeypatch.setattr(runner, 'stock_screen', stock)
    def check(config, source, output, steps):
        assert source.name == 'audited_state.json'
        assert steps == ['OpenROAD.CheckAntennas']
        stage = output/'1-openroad-checkantennas'; stage.mkdir(parents=True)
        (stage/'or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets': antenna_count, 'antenna__violating__pins': antenna_count}))
    monkeypatch.setattr(runner, 'run_step', check)
    def margin(paths):
        assert len(paths) == 3 and all('/timing/after-' in str(p) for p in paths)
        return {'estimated_margin_pass': True}
    monkeypatch.setattr(runner, 'measure', margin)
    if antenna_count:
        with pytest.raises(ValueError): runner.main(final_antenna_repair=True)
    else:
        runner.main(final_antenna_repair=True)
    gate = json.loads((root/'gates.json').read_text())
    assert gate['qualified'] is (antenna_count == 0)
    assert gate['stock_sequence'] is False and gate['final_native_antenna_repair'] is True
    assert gate['final_timing_root'] == str(root/'timing')
    assert json.loads((root/'recipe.json').read_text())['stock_sequence'] is False
