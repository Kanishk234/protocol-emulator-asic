"""Do not move source clock/data instances while restoring the known fanout fix."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_prects_fanout as repair


def test_source_count_guard_and_original_lock_restore():
    text=repair.editor(3645)
    assert 'dict size $original_instances] != 3645' in text
    assert 'original_movable_count != 3644' in text
    assert 'setPlacementStatus FIRM' in text
    assert 'setPlacementStatus [lindex $expected 3]' in text
    assert text.index('setPlacementStatus FIRM')<text.index('catch {detailed_placement}')
    with pytest.raises(ValueError):repair.editor(3596)


def test_no_original_orientation_change_accepted(monkeypatch):
    old=''.join(f'INST\tcell{i}\tbuffer\t0 0\tR0\tPLACED\n' for i in range(3645))
    new=old.replace('cell7\tbuffer\t0 0\tR0','cell7\tbuffer\t0 0\tMY')
    monkeypatch.setattr(repair.cfg,'verify_connections',lambda a,b:{'contracted_connectivity_exact':True})
    with pytest.raises(ValueError,match='moved or changed'):repair.immutability(old,new)


def test_native_producer_count_is_pinned_and_originals_are_locked(monkeypatch):
    monkeypatch.setattr(repair,'INSTANCE_COUNT',3670)
    script=repair.editor(3670)
    assert 'dict size $original_instances] != 3670' in script
    assert '3669' in script
    with pytest.raises(ValueError):
        repair.editor(3645)
