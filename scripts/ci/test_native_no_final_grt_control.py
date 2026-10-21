import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest
import yaml
import native_no_final_grt_control as trial


def config():
    return dict(CLOCK_PERIOD=20, PL_TARGET_DENSITY_PCT=56, SYNTH_STRATEGY='AREA 1',
                GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=150,
                GRT_DESIGN_REPAIR_MAX_SLEW_PCT=55, GRT_DESIGN_REPAIR_MAX_CAP_PCT=55,
                GRT_RESIZER_HOLD_SLACK_MARGIN=.125, GRT_RESIZER_SETUP_SLACK_MARGIN=0,
                GRT_ALLOW_CONGESTION=False, GRT_ANTENNA_REPAIR_MARGIN=50,
                PNR_CORNERS=list(trial.CORNERS), RSZ_CORNERS=list(trial.CORNERS),
                PNR_SDC_FILE=str(Path('src/signoff.sdc').resolve()),
                SIGNOFF_SDC_FILE=str(Path('src/signoff.sdc').resolve()))


@pytest.mark.parametrize('setting', ['omitted', True, False, None, 1])
def test_only_the_stock_final_reroute_option_changes(setting):
    before=config()
    if setting != 'omitted':before['GRT_RESIZER_RUN_GRT']=setting
    saved=copy.deepcopy(before)
    if setting == 'omitted' or setting is True:
        after=trial.configure(before)
        assert {k for k in after if after[k] != before.get(k)} == {'GRT_RESIZER_RUN_GRT'}
        assert after['GRT_RESIZER_RUN_GRT'] is False
    else:
        with pytest.raises(ValueError):trial.configure(before)
    assert before == saved


@pytest.mark.parametrize('key', list(config()))
def test_wrong_physical_policy_or_constraints_rejected(key):
    original=config();original[key]='wrong'
    with pytest.raises(ValueError):trial.configure(original)


def coverage(corner, missing=0):
    return (f'TRIPWIRE_ROUTE_COVERAGE_BEGIN {corner}\n'
            + ('MISSING_NET_HEX 6e6574\n' if missing else '')
            + f'SIGNAL_NETS 10\nGUIDE_NETS {9-missing}\nWIRE_ONLY_NETS 1\nMISSING_NETS {missing}\n'
            + 'TRIPWIRE_ROUTE_COVERAGE_END\n')


@pytest.mark.parametrize('fault', [None,'missing','marker','count','duplicate'])
def test_route_coverage_is_checked_not_assumed(fault):
    c=trial.CORNERS[0];report=coverage(c, int(fault=='missing'))
    if fault=='marker':report=report.replace(c,'wrong')
    if fault=='count':report=report.replace('GUIDE_NETS 9','GUIDE_NETS 8')
    if fault=='duplicate':report+='GUIDE_NETS 9\n'
    if fault in ('marker','count','duplicate'):
        with pytest.raises(ValueError):trial.routing_objects(report,c)
    else:assert trial.routing_objects(report,c)['MISSING_NETS']==int(fault=='missing')


@pytest.mark.parametrize('fault',[None,'setup','electrical','routing','mutated','wrong_source'])
def test_full_control_never_authorizes_route_even_if_measured_gates_pass(tmp_path,monkeypatch,fault):
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('PDK_ROOT','/pdk')
    Path('src').mkdir();Path('src/config_native_stock.json').write_text(json.dumps(config()))
    source=Path('runs/native-stock-screen/flow')/trial.SOURCE_STAGE
    source.mkdir(parents=True);odb=source/'tt_um_tripwire.odb';odb.write_bytes(b'original')
    (source/'state_out.json').write_text(json.dumps({'odb':str(odb.resolve())}))
    monkeypatch.setattr(trial,'SOURCE_ODB_HASH',hashlib.sha256(b'original').hexdigest())
    if fault=='wrong_source':odb.write_bytes(b'wrong')
    original_read=Path.read_text
    def read(p,*args,**kwargs):
        if str(p)=='/tmp/native-source-run.json':return '{}'
        return original_read(p,*args,**kwargs)
    monkeypatch.setattr(Path,'read_text',read)
    monkeypatch.setattr(trial,'validate',lambda *a:None)
    calls=[]
    def run_step(cfg,state,output,steps):
        assert cfg['GRT_RESIZER_RUN_GRT'] is False
        calls.append(steps);output.mkdir(parents=True)
        for i,step in enumerate(steps):
            stage=output/f'{i+1}-{step.lower().replace(".","-")}'
            stage.mkdir();(stage/'state_out.json').write_text('{}')
            if 'ResizerTiming' in step:(stage/'openroad-resizertimingpostgrt.log').write_text('checked separately')
            if step=='OpenROAD.CheckAntennas':(stage/'or_metrics_out.json').write_text('{}')
    monkeypatch.setattr(trial,'run_step',run_step)
    monkeypatch.setattr(trial,'validate_overflow',lambda *a:None)
    monkeypatch.setattr(trial,'check_post_antenna_command',lambda *a:None)
    monkeypatch.setattr(trial,'audit_post_antenna',lambda before,after,timing:after)
    def screen(path,state,output,*args,**kwargs):
        assert path.parent==Path('src') and kwargs['sdc']==Path('src/signoff.sdc')
        assert kwargs['repaired']==state
        output.mkdir();(output/'comparison.json').write_text('{}')
        for c in trial.CORNERS:
            stage=output/f'after-{c}'/'1-openroad-stamidpnr';stage.mkdir(parents=True)
            (stage/'checks.rpt').write_text('electrical')
            slack=3.0 if fault=='setup' else 3.8
            (stage/'capture_setup.rpt').write_text('Startpoint: latch\nEndpoint: ff (rising edge-triggered flip-flop)\nPath Type: max\n'+f' {slack} slack (MET)\n')
            (stage/'route_coverage.rpt').write_text(coverage(c,int(fault=='routing')))
        if fault=='mutated':odb.write_bytes(b'mutated')
    monkeypatch.setattr(trial,'screen',screen)
    monkeypatch.setattr(trial,'measure',lambda paths:{})
    monkeypatch.setattr(trial,'evaluate',lambda *a:{'qualified':fault!='electrical'})
    if fault in ('mutated','wrong_source'):
        with pytest.raises(ValueError):trial.main()
        assert not (trial.OUTPUT/'gates.json').exists()
        return
    trial.main()
    gate=json.loads((trial.OUTPUT/'gates.json').read_text())
    assert gate['qualified'] is False and gate['route_authorized'] is False
    assert gate['diagnostic_only'] is True and gate['official_signoff'] is False
    assert gate['clean_synthesis'] is False and gate['reproduction_required'] is True
    assert gate['routing_completeness_proven'] is False
    assert gate['checkpoint_measured_gates_pass'] is (fault is None)
    assert gate['minimum_slow_capture_setup_ns']==3.5
    assert calls==[['OpenROAD.ResizerTimingPostGRT','OpenROAD.RepairAntennas'],['OpenROAD.CheckAntennas']]
    assert odb.read_bytes()==b'original'


def test_workflow_binds_source_and_exports_control_gate_receipt():
    root=Path(__file__).resolve().parents[2]
    job=yaml.safe_load((root/'.github/workflows/gds-native-no-final-grt-control.yaml').read_text())['jobs']['harden']
    download=next(s for s in job['steps'] if 'download-artifact@' in s.get('uses',''))['with']
    assert download['run-id']==trial.PROFILE['source_run']
    assert download['name']==f"gds-native-lane-mask-setup-reserve-area1-{trial.PROFILE['source_run']}"
    commands='\n'.join(s.get('run','') for s in job['steps'])
    assert 'native_no_final_grt_control.py' in commands
    assert 'native_lane_mask_stage_probe.py' not in commands
    assert 'native_arithmetic_screen.py' not in commands


def test_route_coverage_tcl_counts_real_branch_cases(tmp_path):
    tcl = shutil.which('tclsh') or shutil.which('tclsh8.6')
    if tcl is None:
        pytest.skip('Tcl interpreter unavailable; Python policy/coverage tests still run')
    root=Path(__file__).resolve().parents[2]
    text=(root/'scripts/ci/native_no_final_grt_audit.tcl').read_text()
    body=text[text.index('# Diagnostic route coverage'):]
    setup='''namespace eval ord {proc get_db_block {} {return block}}
proc block {method} {return {guide wire missing power singleton}}
proc fake_net {name method} {
    switch $method {
        getName {return $name}
        getSigType {if {$name eq "power"} {return POWER}; return SIGNAL}
        getITerms {if {$name eq "singleton"} {return {a}}; return {a b}}
        getBTerms {return {}}
        getGuides {if {$name eq "guide"} {return {g}}; return {}}
        getWire {if {$name eq "wire"} {return wire_object}; return NULL}
        default {error "unexpected method $method"}
    }
}
foreach name {guide wire missing power singleton} {
    interp alias {} $name {} fake_net $name
}
'''
    setup+=f'set ::env(STEP_DIR) {{{tmp_path}}}\nset corner_name {trial.CORNERS[0]}\n'
    # Tcl's interactive stdin loop can return zero after script errors. Execute
    # a file and parse its checked receipt, so partial execution cannot pass.
    script=tmp_path/'coverage_test.tcl';script.write_text(setup+body)
    subprocess.run([tcl,str(script)],text=True,check=True,capture_output=True)
    counts=trial.routing_objects((tmp_path/'route_coverage.rpt').read_text(),trial.CORNERS[0])
    assert counts==dict(SIGNAL_NETS=3,GUIDE_NETS=1,WIRE_ONLY_NETS=1,MISSING_NETS=1)
