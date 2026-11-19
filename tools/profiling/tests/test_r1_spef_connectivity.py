from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spef_connectivity import inspect_spef


def fixture(resistors):
    return ('*NAME_MAP\n*1 n\n*2 driver\n*3 load\n*D_NET *1 0.01\n'
            '*CONN\n*I *2:X O\n*I *3:A I\n*CAP\n1 *2:X 0.01\n'
            '*RES\n'+resistors+'\n*END\n')


def test_present_conn_and_cap_records_do_not_prove_a_driver_to_load_path():
    broken=inspect_spef(fixture('1 *2:X *1:1 2\n2 *3:A *1:2 3'))
    assert not broken['passed'] and broken['disconnected_nets']==[dict(net='n',terminals=2,terminal_components=2)]
    fixed=inspect_spef(fixture('1 *2:X *1:1 2\n2 *3:A *1:2 3\n3 *1:1 *1:2 1'))
    assert fixed['passed'] and fixed['terminal_component_histogram']=={1:1}


@pytest.mark.parametrize('text',[fixture('').replace('*END\n',''),fixture('1 *2:X *3:A -1'),fixture('1 *2:X *3:A 2').replace('*I *3:A I','*I *2:X I')])
def test_incomplete_or_ambiguous_resistor_evidence_fails(text):
    with pytest.raises(ValueError):inspect_spef(text)
