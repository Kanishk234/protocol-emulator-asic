import pytest
from pathlib import Path
import extracted_setup_margin as study
from event_nor2_screen import logical_cells


@pytest.mark.parametrize('case',list(study.CASES))
def test_only_reviewed_second_cone_masters_change(monkeypatch,case):
    monkeypatch.setattr(study.base,'TARGETS',study.TARGETS)
    monkeypatch.setattr(study.base,'EXTRA_VARIANTS',{'hold12828':{'sg13cmos5l_dlygate4sd1_1'}})
    text='\n'.join(f'{old} {name} (.A(a), .X(x));' for name,(old,new) in study.TARGETS.items())
    old=logical_cells(text);changes=study.CASES[case];new=logical_cells(study.base.change_netlist(text,changes))
    assert set(new)==set(old)
    for name,(master,pins) in new.items():assert (master,pins)==(changes.get(name,old[name][0]),old[name][1])


def test_second_delay_cannot_be_bypassed(monkeypatch):
    monkeypatch.setattr(study.base,'TARGETS',study.TARGETS)
    monkeypatch.setattr(study.base,'EXTRA_VARIANTS',{'hold12828':{'sg13cmos5l_dlygate4sd1_1'}})
    with pytest.raises(ValueError):study.base.change_netlist('sg13cmos5l_dlygate4sd3_1 hold12828 (.A(a), .X(x));',{'hold12828':'sg13cmos5l_buf_1'})


def test_frontier_workflow_is_manual_and_same_source():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-extracted-setup-margin.yaml';w=yaml.safe_load(p.read_text())
    assert set(w.get('on',w.get(True)))=={'workflow_dispatch'}
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38305592967
    assert any(s.get('run')=='python workflow-src/scripts/ci/extracted_setup_margin.py' for s in steps)
