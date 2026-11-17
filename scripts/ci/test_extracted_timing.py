import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from extracted_timing import route_checkpoint, preserve_signoff_constraints


def test_timeout_is_not_a_route_checkpoint(tmp_path):
    with pytest.raises(ValueError, match="completed DRT state"):
        route_checkpoint(tmp_path)


def test_route_markers_block_extraction(tmp_path):
    stage = tmp_path / "1-openroad-detailedrouting"
    stage.mkdir()
    (stage / "state_out.json").write_text(json.dumps({"metrics": {"route__drc_errors": 215}}))
    with pytest.raises(ValueError, match="zero route DRC"):
        route_checkpoint(tmp_path)


def test_completed_clean_route_files_are_required(tmp_path):
    stage = tmp_path / "1-openroad-detailedrouting"
    stage.mkdir()
    saved = tmp_path / "saved"
    saved.write_text("checkpoint")
    state = {"metrics": {"route__drc_errors": 0},
             **{key: str(saved) for key in ("odb", "def", "nl", "pnl")}}
    path = stage / "state_out.json"
    path.write_text(json.dumps(state))
    assert route_checkpoint(tmp_path) == path
    saved.unlink()
    with pytest.raises(ValueError, match="Missing final route"):
        route_checkpoint(tmp_path)


def test_effective_constraints_survive_source_removal_and_differ_from_inherited(tmp_path):
    import hashlib
    source = tmp_path / 'signoff.sdc'
    source.write_bytes(b'create_clock -period 20 [get_ports clk]\n# Live config paths timed\n')
    output = tmp_path / 'evidence'
    output.mkdir()
    inherited = output / 'inherited.sdc'
    inherited.write_text('set_false_path -setup -to [get_pins config/D]\n')
    original = source.read_bytes()
    saved = preserve_signoff_constraints(source, output)
    source.unlink()
    assert saved.read_bytes() == original
    assert saved.read_bytes() != inherited.read_bytes()
    identity = json.loads((output / 'constraint_identity.json').read_text())
    assert identity['sha256'] == hashlib.sha256(original).hexdigest()
    assert identity['sta_constraint_file'] == str(saved)
    assert identity['inherited_state_sdc_is_signoff_evidence'] is False


def test_stock_constraints_do_not_copy_legacy_hold_override(tmp_path):
    from extracted_timing import stock_signoff_constraints
    path = stock_signoff_constraints({'CLOCK_UNCERTAINTY_CONSTRAINT': 0.25}, tmp_path)
    assert path.read_text() == "source $::env(SCRIPTS_DIR)/base.sdc\n"
    receipt = json.loads((tmp_path / 'constraint_identity.json').read_text())
    assert not receipt['legacy_source_sdc_used'] and not receipt['official_signoff']
    for config in ({'CLOCK_UNCERTAINTY_CONSTRAINT': 0.1}, {'PNR_SDC_FILE': 'custom.sdc'}):
        with pytest.raises(ValueError):
            stock_signoff_constraints(config, tmp_path)


@pytest.mark.parametrize('value', ['0.250000', '-0.250000'])
def test_stock_report_requires_actual_uncertainty(value):
    from extracted_timing import check_stock_report_uncertainty
    check_stock_report_uncertainty(f" {value} 0.933253 clock uncertainty")
    for text in ('', ' 0.100000 0.933253 clock uncertainty',
                 f' {value} 0.933253 clock uncertainty\n 0.100000 1.234567 clock uncertainty'):
        with pytest.raises(ValueError):
            check_stock_report_uncertainty(text)


def test_stock_extraction_collects_actual_functional_reports(tmp_path,monkeypatch):
    import extracted_timing as module
    monkeypatch.chdir(tmp_path)
    src=tmp_path/'src';src.mkdir()
    (src/'config_merged.json').write_text(json.dumps({'CLOCK_PERIOD':20}))
    route=tmp_path/'route';stage=route/'1-openroad-detailedrouting';stage.mkdir(parents=True)
    path=stage/'chip.v';path.write_text('route')
    (stage/'state_out.json').write_text(json.dumps({'metrics':{'route__drc_errors':0},**{k:str(path) for k in ('odb','def','nl','pnl')}}))
    monkeypatch.setenv('PDK_ROOT','/pdk')
    corners=('nom_fast_1p32V_m40C','nom_slow_1p08V_125C','nom_typ_1p20V_25C')
    def run(command,**kwargs):
        cfg=json.loads((src/'config_extracted_timing.json').read_text())
        assert cfg['STA_EXTRA_CORNER_TCL_FILE'].endswith('functional_setup_frontier.tcl')
        assert Path(cfg['SIGNOFF_SDC_FILE']).read_text()=='source $::env(SCRIPTS_DIR)/base.sdc\n'
        out=tmp_path/'runs/extracted-timing/10-openroad-stapostpnr';out.mkdir()
        metrics={}
        for c in corners:
            d=out/c;d.mkdir()
            for name in ('max.rpt','min.rpt'):(d/name).write_text('0.250 19.750 clock uncertainty\n')
            for kind,suffix in (('setup','max'),('hold','min')):
                (d/f'ws.{suffix}.rpt').write_text(c)
                metrics[f'timing__{kind}__ws__corner:{c}']=.2
                metrics[f'timing__{kind}_vio__count__corner:{c}']=0
            (d/'functional_setup_frontier.rpt').write_text(f'TRIPWIRE_FUNCTIONAL_SETUP {c}\nFLOP_DATA_ENDPOINTS 2418\nOUTPUT_ENDPOINTS 24\n1.25 slack (MET)\n')
        (out/'state_out.json').write_text(json.dumps({'metrics':metrics}))
    monkeypatch.setattr(module.subprocess,'run',run)
    monkeypatch.setattr(module,'audit_corners',lambda *args:{c:{'no_reported_electrical_violations':True} for c in corners})
    module.main(route,stock_constraints=True,functional_setup=True)
    rows=json.loads((tmp_path/'runs/extracted-timing/functional_setup.json').read_text())
    assert set(rows)==set(corners)
    assert all(r['worst_reported_setup_slack_ns']==1.25 for r in rows.values())
