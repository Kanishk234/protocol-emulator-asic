import hashlib
import pytest
import fanout_sram_plan as planner


@pytest.mark.parametrize('changed', ['layout', 'netlist'])
def test_source_fingerprints_reject_wrong_checkpoint(tmp_path, monkeypatch, changed):
    nl=tmp_path/'chip.v'; layout=tmp_path/'chip.def'
    nl.write_text('baseline');layout.write_text('layout')
    monkeypatch.setattr(planner,'NL_SHA',hashlib.sha256(nl.read_bytes()).hexdigest())
    monkeypatch.setattr(planner,'DEF_SHA',hashlib.sha256(layout.read_bytes()).hexdigest())
    (nl if changed=='netlist' else layout).write_text('different checkpoint')
    with pytest.raises(ValueError,match='Unreviewed routed'):
        planner.plan(nl,layout)


def test_matching_hashes_do_not_accept_missing_target(tmp_path, monkeypatch):
    nl=tmp_path/'chip.v';layout=tmp_path/'chip.def'
    nl.write_text('sg13cmos5l_buf_4 other (.A(a), .X(b));');layout.write_text('layout')
    monkeypatch.setattr(planner,'NL_SHA',hashlib.sha256(nl.read_bytes()).hexdigest())
    monkeypatch.setattr(planner,'DEF_SHA',hashlib.sha256(layout.read_bytes()).hexdigest())
    with pytest.raises(ValueError,match='Wrong SRAM target connectivity'):
        planner.plan(nl,layout)
