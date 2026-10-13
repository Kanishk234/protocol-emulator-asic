"""The copied placement script may change only the congestion estimator flag."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'test_internal'))
import cloud_prects_native_estimator as native


def test_only_estimator_flag_changes_and_header_survives(tmp_path,monkeypatch):
    original=tmp_path/'gpl.tcl'
    original.write_text('# Copyright fixture\n# Apache2.0 fixture\n'+native.ANCHOR+'\nwrite_views\n')
    monkeypatch.setattr(native,'GPL_SHA',native.cfg.sha(original))
    copied=native.instrument(original,tmp_path/'copy')
    assert copied.read_text().replace(native.INSERT,'',1)==original.read_text()
    assert copied.read_text().startswith('# Copyright fixture\n# Apache2.0 fixture\n')
    assert copied.read_text().count(native.INSERT)==1


def test_wrong_source_or_duplicate_command_rejected(tmp_path,monkeypatch):
    original=tmp_path/'gpl.tcl';original.write_text(native.ANCHOR+'\n'+native.ANCHOR+'\n')
    monkeypatch.setattr(native,'GPL_SHA',native.cfg.sha(original))
    with pytest.raises(ValueError,match='Nonunique'):native.instrument(original,tmp_path/'copy')
    monkeypatch.setattr(native,'GPL_SHA','0'*64)
    with pytest.raises(ValueError,match='Pinned'):native.instrument(original,tmp_path/'copy')


def test_resolved_defaults_match_control_but_changed_capacity_is_rejected():
    control=dict(native.ROUTING_POLICY)
    native.verify_routing_policy(dict(control),control)
    changed=dict(control,GRT_ADJUSTMENT=0.4)
    with pytest.raises(ValueError,match='GRT_ADJUSTMENT'):
        native.verify_routing_policy(changed,control)
    with pytest.raises(ValueError,match='GRT_ADJUSTMENT'):
        native.verify_routing_policy(changed,changed)
