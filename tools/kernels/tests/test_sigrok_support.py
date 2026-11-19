"""Decoder selection must preserve other protocols and reject silent bypass."""
import hashlib
import json

import pytest
import sigrok_support as support


def test_only_ps2_overrides_the_decoder_search_path(monkeypatch):
    monkeypatch.setenv('SIGROKDECODE_DIR','existing-user-path')
    assert support.decoder_environment('spi:clk=sck')['SIGROKDECODE_DIR']=='existing-user-path'
    assert support.decoder_environment('ps2:clk=clk:data=data')['SIGROKDECODE_DIR']==str(support.PS2_VENDOR)


def test_changed_pinned_decoder_is_rejected_before_use(tmp_path,monkeypatch):
    source=tmp_path/'pd.py';source.write_text('original')
    row={'files':{'pd.py':{'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}}}
    (tmp_path/'PROVENANCE.json').write_text(json.dumps(row))
    monkeypatch.setattr(support,'PS2_VENDOR',tmp_path)
    source.write_text('changed')
    with pytest.raises(ValueError,match='changed'):
        support.decoder_environment('ps2:clk=clk:data=data')


def test_required_decoding_cannot_be_silently_disabled(monkeypatch):
    monkeypatch.setenv('TRIPWIRE_SKIP_SIGROK','1')
    assert support.decode('unused.vcd','spi') is None
    with pytest.raises(RuntimeError,match='Required'):
        support.decode('unused.vcd','ps2',required=True)
