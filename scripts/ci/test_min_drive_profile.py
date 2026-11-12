from copy import deepcopy
import json
from pathlib import Path

import pytest

from host_idle_portable_trials import select
from min_drive_profile import EXCLUDED, prepare
from stock_profile_effective import validate
from test_host_idle_portable_trials import reference
from test_stock_profile_effective import fixture


def prepared(root):
    config, selected = reference()
    config, selected = select(config, selected, 'clock75_hold125')
    selected['c_pad_decode'] = True
    (root/'src').mkdir()
    (root/'spikes/phase2_stock_flow').mkdir(parents=True)
    (root/'src/config.json').write_text(json.dumps(config, indent=2)+'\n')
    (root/'spikes/phase2_stock_flow/selected_profile.json').write_text(json.dumps(selected))
    return deepcopy(config)


def test_only_cell_exclusion_changes_and_reapplication_rejects(tmp_path):
    before = prepared(tmp_path)
    receipt = prepare(tmp_path)
    after = json.loads((tmp_path/'src/config.json').read_text())
    assert {k:v for k,v in after.items() if before.get(k)!=v} == {'EXTRA_EXCLUDED_CELLS': EXCLUDED}
    assert after['CLOCK_PERIOD'] == 20 and after['GRT_RESIZER_SETUP_SLACK_MARGIN'] == 0
    assert receipt['changed_fields'] == ['EXTRA_EXCLUDED_CELLS']
    with pytest.raises(ValueError, match='Wrong source'):
        prepare(tmp_path)


def test_wrong_source_rejects_before_mutation(tmp_path):
    prepared(tmp_path)
    p=tmp_path/'src/config.json'
    p.write_text(p.read_text()+' ')
    before=p.read_bytes()
    with pytest.raises(ValueError, match='Wrong source'):
        prepare(tmp_path)
    assert p.read_bytes()==before


@pytest.mark.parametrize('stage', ['synthesis', 'final'])
@pytest.mark.parametrize('bad', [None, *EXCLUDED])
def test_actual_mapping_and_final_exclusions(tmp_path, stage, bad):
    selected=fixture(tmp_path, {'EXTRA_EXCLUDED_CELLS': EXCLUDED,
                               'SYNTH_BUFFER_CELL':'sg13cmos5l_buf_2/A/X'}, late=.125)
    synth=tmp_path/'06-yosys-synthesis'
    synth.mkdir()
    good='\n'.join(f'{m} u{i} (.A(a), .X(z));' for i,m in enumerate(
        ['sg13cmos5l_buf_2','sg13cmos5l_nand2_2','sg13cmos5l_nor3_2']))
    final=tmp_path/'44-openroad-resizertimingpostgrt'
    (synth/'tt_um_tripwire.nl.v').write_text(good)
    (final/'tt_um_tripwire.nl.v').write_text(good)
    if bad:
        path=(synth if stage=='synthesis' else final)/'tt_um_tripwire.nl.v'
        path.write_text(path.read_text()+f'\n{bad} wrong (.A(a), .X(z));')
        with pytest.raises(ValueError, match='Excluded cell remains'):
            validate(tmp_path,selected)
    else:
        assert validate(tmp_path,selected)['native_gate_exclusions_verified'] is True
