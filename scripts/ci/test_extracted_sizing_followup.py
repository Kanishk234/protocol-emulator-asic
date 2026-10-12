import pytest
from pathlib import Path
import extracted_sizing_followup as followup
from event_nor2_screen import logical_cells


def configure(monkeypatch):
    base=followup.base
    monkeypatch.setattr(base,'TARGETS',followup.TARGETS)
    monkeypatch.setattr(base,'CASES',followup.CASES)
    monkeypatch.setattr(base,'EXTRA_VARIANTS',{'hold12828':{'sg13cmos5l_dlygate4sd1_1'}})
    return base


@pytest.mark.parametrize('case',list(followup.CASES))
def test_shorter_delay_changes_only_reviewed_cells_and_preserves_all_pins(monkeypatch,case):
    base=configure(monkeypatch)
    text='\n'.join(f'{old} {name} (.A(a), .X(x));' for name,(old,new) in followup.TARGETS.items())
    old=logical_cells(text);changes=followup.CASES[case];new=logical_cells(base.change_netlist(text,changes))
    assert set(old)==set(new)
    for n,(m,pins) in new.items():assert (m,pins)==(changes.get(n,old[n][0]),old[n][1])


def test_delay_bypass_and_arbitrary_variants_are_refused(monkeypatch):
    base=configure(monkeypatch);text='sg13cmos5l_dlygate4sd3_1 hold12828 (.A(a), .X(x));'
    for master in ('sg13cmos5l_buf_1','sg13cmos5l_inv_1','missing'):
        with pytest.raises(ValueError):base.change_netlist(text,{'hold12828':master})


def test_workflow_is_manual_uses_same_extracted_source_and_never_routes():
    import yaml
    root=Path(__file__).resolve().parents[2];p=root/'.github/workflows/gds-extracted-sizing-followup.yaml';w=yaml.safe_load(p.read_text())
    assert set(w.get('on',w.get(True)))=={'workflow_dispatch'}
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38305592967
    assert any(s.get('run')=='python workflow-src/scripts/ci/extracted_sizing_followup.py' for s in steps)
    assert "base.main(Path('runs/extracted-sizing-followup'))" in (root/'scripts/ci/extracted_sizing_followup.py').read_text()
