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
