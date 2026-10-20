"""Frozen physical candidates must not inherit main's resource tables."""
import shutil
import subprocess

from verify_timing_trial import CANDIDATE, ROOT, regenerate_python_tables


def test_frozen_tables_match_candidate_without_rewriting_rtl(tmp_path):
    (tmp_path / 'tools/gen').mkdir(parents=True)
    (tmp_path / 'spec').mkdir()
    (tmp_path / 'src').mkdir()
    shutil.copyfile(ROOT / 'tools/gen/gen.py', tmp_path / 'tools/gen/gen.py')
    spec = subprocess.check_output(['git', 'show', f'{CANDIDATE}:spec/tripwire.yaml'], cwd=ROOT)
    (tmp_path / 'spec/tripwire.yaml').write_bytes(spec)
    (tmp_path / 'tools/tripwire_spec.py').write_text('stale main resource tables')
    sentinel = tmp_path / 'src/trw_defs.vh'
    sentinel.write_text('archived RTL must remain exact')
    regenerate_python_tables(tmp_path)
    tables = {}
    exec((tmp_path / 'tools/tripwire_spec.py').read_text(), tables)
    assert len(tables['PIN_UNIT_FEATURES']) == 4
    assert len(tables['FABRIC_PRODUCERS']) == 9
    assert len(tables['FABRIC_CONSUMERS']) == 9
    assert tables['FABRIC_PRODUCERS'][-1] == 'HOST_IN'
    assert sentinel.read_text() == 'archived RTL must remain exact'


def test_trial_matches_current_firmware_to_current_tests_on_frozen_rtl(tmp_path,monkeypatch):
    import verify_timing_trial as target
    real_run=subprocess.run
    def run(command,*args,**kwargs):
        if command[0]=='yosys':
            return subprocess.CompletedProcess(command,0)
        return real_run(command,*args,**kwargs)
    monkeypatch.setattr(target.subprocess,'run',run)
    output=tmp_path/'trial'
    target.verify('bs-resync-event',output)
    expected_program=subprocess.check_output(['git','show','HEAD:programs/ws2812.trw'],cwd=ROOT)
    expected_test=subprocess.check_output(['git','show','HEAD:test_internal/chip/test_l3.py'],cwd=ROOT)
    assert (output/'programs/ws2812.trw').read_bytes()==expected_program
    assert (output/'test_internal/chip/test_l3.py').read_bytes()==expected_test
    assert b'tx_lentok=true' in expected_program and b'0xB000' in expected_test
    frozen_defs=subprocess.check_output(['git','show',f'{CANDIDATE}:src/trw_defs.vh'],cwd=ROOT)
    assert (output/'src/trw_defs.vh').read_bytes()==frozen_defs
