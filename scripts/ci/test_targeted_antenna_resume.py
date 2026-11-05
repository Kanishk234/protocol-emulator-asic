"""Recovery must begin with readback, never repeat physical edits or routing."""
import hashlib
import json
import pytest
import targeted_antenna_diagnostic as diagnostic


def test_resume_starts_with_read_only_export(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'src').mkdir()
    (tmp_path / 'src/config_merged.json').write_text('{}')
    original = tmp_path / 'original.v'
    original.write_text('sg13cmos5l_buf_2 wire13568 (.A(a), .X(b));')
    source = tmp_path / 'source.json'
    source.write_text(json.dumps({'nl': str(original)}))
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'source_state': str(source), 'files': {
        str(source): hashlib.sha256(source.read_bytes()).hexdigest()}}))
    plan = tmp_path / 'spikes/phase2_stock_flow'
    plan.mkdir(parents=True)
    (plan / 'antenna_targeted_sizing_feasibility.json').write_text(json.dumps({'cases': [
        {'instance': 'wire13568', 'original_master': 'sg13cmos5l_buf_2', 'candidate_master': 'sg13cmos5l_buf_8'}]}))
    final = tmp_path / 'runs/targeted-diagnostic/routing/1-openroad-globalrouting'
    final.mkdir(parents=True)
    (final / 'state_out.json').write_text('{}')
    monkeypatch.setenv('SOURCE_MANIFEST', str(manifest))
    def stop_at_readback(config, source, output, steps):
        assert steps == ['OpenROAD.STAMidPNR']
        assert config['STA_EXTRA_CORNER_TCL_FILE'].endswith('/readback.tcl')
        assert output.name == 'readback'
        raise RuntimeError('Verified readback first')
    monkeypatch.setattr(diagnostic, 'run_step', stop_at_readback)
    with pytest.raises(RuntimeError, match='Verified readback first'):
        diagnostic.main(True, resume=True)
