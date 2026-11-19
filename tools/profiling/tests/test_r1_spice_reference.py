from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'spikes/r1'))
from spice_reference import model_ports,parse_and_verify,render,substitute_schematic_input


def source_fixture():
    shapes={'data':dict(direction='input',bits=list(range(1,447))), 'out':dict(direction='output',bits=[447])}
    module=dict(ports=shapes,cells={'tile/_1_':dict(type='INV',connections={'A':[1],'Y':[447]})})
    models=model_ports('.subckt INV Y A VDD VSS\n.ends\n')
    ports={f'data[{i}]':'n'+str(i+1) for i in range(446)}
    ports.update(out='n447',VPWR='VPWR',VGND='VGND')
    inventory=dict(cells=[['tile/_1_','INV']],terms=[['tile/_1_',p,n] for p,n in [('A','n1'),('Y','n447'),('VDD','VPWR'),('VSS','VGND')]],ports=ports)
    return module,models,inventory,shapes


def test_source_spice_preserves_unused_root_ports_and_actual_model_pin_order():
    module,models,inventory,shapes=source_fixture();text=render(module,models)
    assert 'Xtile/_1_ out data[0] VPWR VGND INV' in text
    assert parse_and_verify(text,models,inventory,shapes)['cells']==1
    for changed in [text.replace('out data[0] VPWR','out data[1] VPWR'),
                    text.replace('out data[0] VPWR VGND','out data[0] VGND VPWR'),
                    text.replace('data[445]','')]:
        with pytest.raises(ValueError):parse_and_verify(changed,models,inventory,shapes)


def test_generated_comparison_keeps_layout_setup_and_original_lvs_command():
    source='set c1 [readnet spice layout.spice]\nreadnet verilog source.v $circuit2\nlvs unchanged command\n'
    changed=substitute_schematic_input(source,'source.v','proven.spice')
    assert changed.replace('readnet spice proven.spice','readnet verilog source.v')==source
    with pytest.raises(ValueError):substitute_schematic_input(source+source,'source.v','proven.spice')
    with pytest.raises(ValueError):model_ports('.subckt INV A A VDD VSS\n.ends\n')
