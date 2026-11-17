import hashlib
import json
from pathlib import Path

import pytest
import yaml

from audit_promotion_inputs import audit


def package(tmp_path):
    for folder in ('src', 'test', 'macro/m', '.github/workflows'):
        (tmp_path / folder).mkdir(parents=True, exist_ok=True)
    (tmp_path / 'info.yaml').write_text(yaml.safe_dump({'project': {
        'tiles': '8x4', 'clock_hz': 50000000, 'top_module': 'tt_um_tripwire',
        'source_files': ['tt_um_tripwire.v', 'trw_chip.v']}}))
    for name in ('tt_um_tripwire.v', 'trw_chip.v', 'macro.v', 'pdn.tcl'):
        (tmp_path / 'src' / name).write_text('fixture\n')
    (tmp_path / 'test/Makefile').write_text('PROJECT_SOURCES = tt_um_tripwire.v trw_chip.v\n# sg13cmos5l_udp.v MACRO_MODELS\n')
    (tmp_path / '.github/workflows/gds.yaml').write_text('unchanged official workflow\n')
    macro = tmp_path / 'macro/m'
    (macro / 'm.gds').write_bytes(b'fixture')
    (macro / 'LICENSE').write_text('fixture license')
    (macro / 'PROVENANCE.json').write_text(json.dumps({'files': {
        'm.gds': hashlib.sha256(b'fixture').hexdigest()}}))
    config = {'CLOCK_PERIOD': 20, 'MACROS': {'m': {'gds': ['dir::../macro/m/m.gds'],
              'nl': ['dir::macro.v']}}, 'PDN_CFG': 'dir::pdn.tcl'}
    (tmp_path / 'src/config.json').write_text(json.dumps(config))
    return tmp_path


def test_input_success_never_implies_adoption_or_signoff(tmp_path):
    root = package(tmp_path)
    result = audit(root, root)
    assert result['input_checks_passed']
    assert not result['adoption_ready'] and not result['official_signoff']


@pytest.mark.parametrize('fault', ['missing_macro', 'license', 'source_list', 'provenance'])
def test_incomplete_or_inconsistent_package_rejected(tmp_path, fault):
    root = package(tmp_path)
    if fault == 'missing_macro':
        (root / 'macro/m/m.gds').unlink()
    elif fault == 'license':
        (root / 'macro/m/LICENSE').unlink()
    elif fault == 'source_list':
        (root / 'test/Makefile').write_text('PROJECT_SOURCES = tt_um_tripwire.v\n')
    else:
        (root / 'macro/m/m.gds').write_bytes(b'changed')
    with pytest.raises(AssertionError):
        audit(root, root)


def test_macro_reference_cannot_escape_checkout(tmp_path):
    root = package(tmp_path)
    p = root / 'src/config.json'
    config = json.loads(p.read_text())
    config['MACROS']['m']['gds'] = ['dir::../../outside.gds']
    p.write_text(json.dumps(config))
    with pytest.raises(AssertionError, match='escapes'):
        audit(root, root)


def test_unreviewed_meta_rejected(tmp_path):
    root=package(tmp_path)
    p=root/'src/config.json';config=json.loads(p.read_text())
    config['meta']={'version':1,'flow':['OpenROAD.DetailedRouting']}
    p.write_text(json.dumps(config))
    with pytest.raises(AssertionError,match='Unreviewed project flow'):audit(root,root)
