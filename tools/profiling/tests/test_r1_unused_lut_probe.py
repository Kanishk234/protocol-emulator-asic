from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'spikes/r1'))
import unused_lut_probe as probe


def fixture():
    spec = {'TileSpecs': {'X2Y3': {'G.FF': {300: '1'}}}}
    module = {'ports': {'FrameData': {'bits': list(range(32))},
                        'FrameStrobe': {'bits': list(range(100, 120))}},
              'cells': {'cfg': {'type': 'sg13cmos5l_dlhq_1',
                                'connections': {'D': [12], 'GATE': [109], 'Q': [200]}}}}
    return [], spec, module, {'cfg': '0'}


@pytest.mark.parametrize('features', [['X2Y3.G.FF'], ['X2Y3.G.INIT_0'],
                                     ['X2Y3.LG_O.E1BEG0']])
def test_used_logic_or_routed_output_cannot_be_parked(features):
    args = fixture(); args = (features, *args[1:])
    with pytest.raises(ValueError, match='used'): probe.parking_bit(*args)


@pytest.mark.parametrize('fault', [None, 'mapping', 'duplicate', 'unknown', 'already_set'])
def test_frame_address_maps_to_exact_observed_native_latch(fault):
    features, spec, module, state = fixture()
    if fault == 'mapping': module['cells']['cfg']['connections']['D'] = [11]
    if fault == 'duplicate': module['cells']['other'] = deepcopy(module['cells']['cfg'])
    if fault == 'unknown': state['cfg'] = 'x'
    if fault == 'already_set': state['cfg'] = '1'
    if fault is None:
        bit = probe.parking_bit(features, spec, module, state)
        assert (bit['frame'], bit['data_bit'], bit['cell']) == (9, 12, 'cfg')
    else:
        with pytest.raises(ValueError): probe.parking_bit(features, spec, module, state)


def source_script(bit):
    pin = bit['tile'] + '/' + bit['cell'] + '/Q'
    return (f'set p [get_pins -quiet {{{pin}}}]\n'
            'if {[llength $p]!=1} {error "missing configuration pin"}\n'
            'set_case_analysis 0 $p\nincr observed\n'
            f'if {{[sta::pin_sim_logic_value [lindex [get_pins {{{pin}}}] 0]]!="0"}} {{error "bad"}}\n')


def test_only_case_bit_and_matching_guard_change():
    bit = probe.parking_bit(*fixture()); text = source_script(bit)
    changed = probe.change_case(text, bit)
    assert changed == text.replace('set_case_analysis 0 $p', 'set_case_analysis 1 $p').replace(']]!="0"', ']]!="1"')
    for bad in (text + text, text.replace('set_case_analysis 0 $p', 'set_case_analysis 1 $p')):
        with pytest.raises(ValueError): probe.change_case(bad, bit)


def metadata():
    run = dict(id=probe.SOURCE_RUN, head_sha=probe.SOURCE_SHA, head_branch='efpga',
               path='.github/workflows/r1_run_timing.yaml', run_attempt=1,
               status='completed', conclusion='failure')
    artifact = dict(id=probe.ARTIFACT_ID, expired=False, name=f'r1-configured-timing-{probe.SOURCE_RUN}',
                    digest='sha256:' + probe.ARCHIVE_SHA,
                    workflow_run=dict(id=probe.SOURCE_RUN, head_sha=probe.SOURCE_SHA))
    return run, artifact


@pytest.mark.parametrize('fault', [None, 'success', 'sha', 'artifact', 'expired'])
def test_exact_retained_failure_is_the_only_control(fault):
    run, artifact = metadata()
    if fault == 'success': run['conclusion'] = 'success'
    if fault == 'sha': run['head_sha'] = 'foreign'
    if fault == 'artifact': artifact['digest'] = 'sha256:' + '0' * 64
    if fault == 'expired': artifact['expired'] = True
    if fault is None: probe.context(run, artifact)
    else:
        with pytest.raises(ValueError): probe.context(run, artifact)


def timing_log(offset):
    rows = ['RUNSTA_CONFIGURATION 8736', 'RUNSTA_CLOSED 8736']
    rows += [f'RUNSTA_FF\tr{i}\tX\t1\tOUT\t0' for i in range(370)]
    rows += [f'RUNSTA_ENDPOINT\tr{i}/D\t{1.508933 + i + offset:.6f}' for i in range(6)]
    return '\n'.join(rows + ['RUNSTA_END', ''])


@pytest.mark.parametrize('supported', [True, False])
def test_complete_negative_or_positive_measurement_never_becomes_acceptance(tmp_path, supported):
    (tmp_path / 'plan.json').write_text(json.dumps(dict(input_sha256={}, scripts_sha256={}, change={})))
    for label in ('control', 'candidate'):
        for policy in ('static', 'dynamic'):
            offset = 0.016122 if policy == 'static' and (label == 'control' or not supported) else 0
            (tmp_path / (label + '_' + policy + '.log')).write_text(timing_log(offset))
    probe.audit(tmp_path)
    result = json.loads((tmp_path / 'result.json').read_text())
    assert result['hypothesis_supported'] is supported
    assert result['timing_acceptance'] is False and result['loaded_candidate_tested'] is False
