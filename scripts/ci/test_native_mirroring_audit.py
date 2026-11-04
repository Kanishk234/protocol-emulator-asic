import pytest
from native_mirroring_audit import require_mirroring

def test_native_unlogged_call_completion():
    assert require_mirroring("[INFO DPL-0020] Mirrored 20500 instances\n") == 20500

def test_zero_is_completed():
    assert require_mirroring("[INFO DPL-0020] Mirrored 0 instances\n") == 0

@pytest.mark.parametrize("text", ["+ optimize_mirroring\n", "# [INFO DPL-0020] Mirrored 20500 instances\n", ""])
def test_missing_completion_rejects(text):
    with pytest.raises(ValueError): require_mirroring(text)
