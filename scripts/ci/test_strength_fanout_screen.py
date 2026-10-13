from pathlib import Path
import hashlib
import pytest
import combined_physical_plan as planner
from test_combined_physical_plan import fixture
from strength_fanout_plan import BINDING
from strength_fanout_screen import PROFILE


def configured(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch)
    cfg=planner.source_binding()
    cfg['setup']=dict(cfg['setup'],edriver0='sg13cmos5l_buf_4')
    cfg['targets']=dict(cfg['targets'],edriver0=('sg13cmos5l_buf_1','sg13cmos5l_buf_4'))
    cfg['resize_only_slew_drivers']=['edriver0']
    return args,cfg


def test_reviewed_slew_resize_retains_loads_and_avoids_extra_buffer(tmp_path,monkeypatch):
    args,cfg=configured(tmp_path,monkeypatch)
    proposal=planner.plan(*args,binding=cfg)
    assert proposal['added_buffers']==47
    assert not any(g['source_net']=='enet0' for g in proposal['groups'])
    assert any(r['instance']=='edriver0' for r in proposal['resizes'])


@pytest.mark.parametrize('fault',['fanout','missing_driver','not_resized'])
def test_resize_only_cannot_skip_other_electrical_failures(tmp_path,monkeypatch,fault):
    args,cfg=configured(tmp_path,monkeypatch)
    if fault=='fanout':
        for corner,text in args[3].items():
            text=text.replace('max fanout\n','max fanout\nedriver0/X 8 9 -1 (VIOLATED)\n')
            args[3][corner]=text
            cfg['checks_sha'][corner]=hashlib.sha256(text.encode()).hexdigest()
    elif fault=='missing_driver':cfg['resize_only_slew_drivers']=['absent']
    else:cfg['setup'].pop('edriver0')
    with pytest.raises(ValueError):planner.plan(*args,binding=cfg)


def test_exact_source_and_manual_strict_screen():
    import yaml
    from fanout_strength_sensitivity import CASES
    assert BINDING['source_run']==38456657314
    assert BINDING['setup']==CASES['pair_electrical']
    assert BINDING['hold_count']==9 and BINDING['hold_target_ns']==.075
    assert BINDING['electrical_nets']==6
    assert PROFILE['post_antenna_audit'] is not None
    root=Path(__file__).resolve().parents[2]
    w=yaml.safe_load((root/'.github/workflows/gds-strength-fanout-screen.yaml').read_text())
    d=next(s for s in w['jobs']['harden']['steps'] if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38456657314
    assert d['with']['name']=='gds-fanout-load-route-38456657314'
    assert 'detailedrouting' not in str(w).lower()
