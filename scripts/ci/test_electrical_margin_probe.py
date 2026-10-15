import copy
from pathlib import Path
import pytest
from electrical_margin_probe import SOURCE_RUN, SOURCE_SHA, validate_source
from electrical_margin_summary import parse

CORNER = 'nom_slow_1p08V_125C'

def report(actual='2.4', count=1):
    return f'''TRIPWIRE_MARGIN_BEGIN {CORNER}
TRIPWIRE_NET_HEX {'net[3]'.encode().hex()}
max slew
Pin Limit Slew Slack
sink/A 2.5 {actual} 0.1 (MET)
max fanout
source/Y 8 8 (MET)
TRIPWIRE_MARGIN_END {CORNER} {count}
'''


def test_near_limit_legal_net_is_visible():
    corner, data = parse(report())
    assert corner == CORNER
    assert data['nets']['net[3]']['slew']['utilization'] == .96
    assert data['near_limit_counts'] == dict(slew=1, fanout=1, capacitance=0)


@pytest.mark.parametrize('text', [report(count=2), report().replace('TRIPWIRE_MARGIN_END', 'missing'),
    report().replace('sink/A 2.5 2.4 0.1 (MET)', 'not a measurement').replace('source/Y 8 8 (MET)', 'missing'),
    report().replace('TRIPWIRE_NET_HEX', 'TRIPWIRE_NET_HEX 00\nTRIPWIRE_NET_HEX') + report()])
def test_incomplete_or_duplicate_probe_fails_closed(text):
    with pytest.raises(ValueError):
        parse(text)


def test_failed_route_source_is_exact():
    run = dict(id=SOURCE_RUN, head_sha=SOURCE_SHA, head_branch='main', conclusion='failure',
               path='.github/workflows/gds-route-reserve-route.yaml')
    gates = dict(qualified=False, source_run=38687129808)
    validate_source(run, gates)
    altered = copy.deepcopy(run); altered['head_sha'] = 'other'
    with pytest.raises(ValueError):
        validate_source(altered, gates)


def test_tcl_is_read_only_and_reports_per_net():
    text = Path(__file__).with_name('electrical_margin_probe.tcl').read_text()
    assert 'foreach tripwire_margin_net [get_nets -hierarchical *]' in text
    assert '-violators' not in text
    assert 'TRIPWIRE_MARGIN_END' in text
    for command in ('repair_design', 'repair_antennas', 'global_route', 'detailed_route', 'set_max_'):
        assert command not in text


def test_paired_drift_finds_new_failure_and_rejects_changed_limit():
    from electrical_margin_summary import paired
    from postgrt_timing import CORNERS
    _, data = parse(report())
    screen = {c: copy.deepcopy(data) for c in CORNERS}
    extracted = copy.deepcopy(screen)
    for c in CORNERS:
        extracted[c]['nets']['net[3]']['slew']['actual'] = 2.6
        extracted[c]['nets']['net[3]']['slew']['utilization'] = 1.04
    result = paired(screen, extracted)
    assert result[CORNER]['newly_failing'][0]['kind'] == 'slew'
    assert result[CORNER]['newly_failing'][0]['drift'] == pytest.approx(.08)
    extracted[CORNER]['nets']['net[3]']['slew']['limit'] = 3
    with pytest.raises(ValueError):
        paired(screen, extracted)


def test_workflow_only_measures_saved_failed_route():
    import yaml
    root = Path(__file__).resolve().parents[2]
    w = yaml.safe_load((root/'.github/workflows/gds-electrical-margin-probe.yaml').read_text())
    steps = w['jobs']['harden']['steps']
    d = next(s for s in steps if 'download-artifact@' in s.get('uses', ''))
    assert d['with']['run-id'] == SOURCE_RUN
    assert d['with']['name'] == 'gds-route-reserve-route-38689478738'
    assert any(s.get('run') == 'python workflow-src/scripts/ci/electrical_margin_probe.py' for s in steps)
    assert len([s for s in steps if 'upload-artifact@' in s.get('uses', '')]) == 1


def test_saved_input_hashes_detect_changes_and_missing_views(tmp_path):
    import json
    from electrical_margin_probe import input_hashes
    netlist = tmp_path/'design.v'; netlist.write_text('original')
    state = tmp_path/'state.json'; state.write_text(json.dumps(dict(nl=str(netlist))))
    before = input_hashes({'screen': state})
    netlist.write_text('changed')
    assert input_hashes({'screen': state}) != before
    netlist.unlink()
    with pytest.raises(ValueError, match='Missing saved probe input'):
        input_hashes({'screen': state})


def test_paired_summary_order_is_stable_across_hash_seeds():
    import os
    import subprocess
    import sys
    code = '''import copy,json
from electrical_margin_summary import paired
from postgrt_timing import CORNERS
row={'slew':{'limit':2.5,'actual':2.0,'utilization':.8}}
a={c:{'nets':{'z':copy.deepcopy(row),'a':copy.deepcopy(row)}} for c in CORNERS}
b=copy.deepcopy(a)
for d in b.values():
 for v in d['nets'].values():v['slew']['utilization']=1.1
print(json.dumps(paired(a,b),sort_keys=True))
'''
    outputs = [subprocess.check_output([sys.executable,'-c',code],
        env=dict(os.environ,PYTHONHASHSEED=str(seed)),text=True) for seed in (1,2)]
    assert outputs[0] == outputs[1]
