from pathlib import Path

import pytest

import verify_drop_parallel as trial


def test_wrong_base_rejected_without_writing_reference(tmp_path):
    (tmp_path/'src').mkdir()
    (tmp_path/'src/trw_chan_port.v').write_text('wrong source')
    with pytest.raises(ValueError, match='Wrong parallel counter source'):
        trial.apply_delta(tmp_path)
    assert not (tmp_path/'drop_parallel_gold.v').exists()


def test_proof_failure_cannot_write_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(trial, 'prepare_lane_mask', lambda *a: None)
    monkeypatch.setattr(trial, 'apply_delta', lambda *a: Path('unused'))
    def fail(*a):
        raise ValueError('unproven counter bits')
    monkeypatch.setattr(trial, 'prove', fail)
    with pytest.raises(ValueError, match='unproven'):
        trial.verify(tmp_path)
    assert not (tmp_path/'drop_parallel_receipt.json').exists()
