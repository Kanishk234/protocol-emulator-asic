from copy import deepcopy
import pytest
from autonomy.r1_balanced_audit import identity,guide_blocks,wire_coverage,power_geometry


def test_incomplete_and_wrong_source_campaigns_cannot_be_promoted():
    expected=('12','a'*40)
    good=dict(id=12,head_sha='a'*40,run_attempt=1,conclusion='success')
    identity(good,expected)
    for key,value in [('conclusion',None),('head_sha','b'*40),('run_attempt',2),('id',13)]:
        bad={**good,key:value}
        with pytest.raises(ValueError):identity(bad,expected)


def test_guides_need_unique_names_and_positive_supported_rectangles():
    good='data[0]\n(\n0 0 100 200 Metal3\n)\n'
    assert list(guide_blocks(good))==['data[0]']
    for text in [good+good,good.replace('100 200','0 200'),good.replace('Metal3','Metal1'),'']:
        with pytest.raises(ValueError):guide_blocks(text)


def test_all_fifty_two_feedthroughs_need_native_identity_and_guides():
    header=dict(cells={},ports={'i':dict(direction='input',bits=list(range(52))),
                                'o':dict(direction='output',bits=list(range(52)))})
    nets={f'{p}[{i}]':f'wire{i}' for i in range(52) for p in ('i','o')}
    guides={f'wire{i}':[['0','0','100','100','Metal2']] for i in range(52)}
    assert wire_coverage(header,nets,guides)==52
    bad=deepcopy(nets);bad['o[51]']='other'
    with pytest.raises(ValueError):wire_coverage(header,bad,guides)
    guides.pop('wire51')
    with pytest.raises(ValueError):wire_coverage(header,nets,guides)
    with pytest.raises(ValueError):wire_coverage({**header,'cells':{'hidden':{}}},nets,guides)


def test_absolute_power_phase_and_full_height_remain_independent_gates():
    boxes=[dict(net='VPWR',layer='Metal4',rect=[10950,0,13050,56700]),
           dict(net='VGND',layer='Metal4',rect=[15050,0,17150,56700])]
    power_geometry(boxes,0,56700)
    bad=deepcopy(boxes);bad[0]['rect'][0]+=1;bad[0]['rect'][2]+=1
    with pytest.raises(ValueError):power_geometry(bad,0,56700)
    bad=deepcopy(boxes);bad[0]['rect'][3]=200
    with pytest.raises(ValueError):power_geometry(bad,0,56700)
