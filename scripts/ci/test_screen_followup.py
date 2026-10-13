import json
from pathlib import Path
import pytest
import combined_physical_screen as engine
from screen_followup import PROFILE
from screen_followup_plan import BINDING,plan


def test_fresh_source_binding_and_strict_gate_are_preserved():
    assert BINDING['source_run']==38347662810
    assert BINDING['hold_count']==47 and BINDING['hold_target_ns']==.075
    assert BINDING['electrical_nets']==2 and not BINDING['setup']
    assert PROFILE['source_kind']=='global-screen'
    assert PROFILE['source_gate_receipt']['qualified'] is False
    assert PROFILE['source_gate_receipt']['minimum_fast_hold_ns']==.05
    with pytest.raises(ValueError,match='Wrong combined source'):
        plan('old','old','old',{},Path('std.lef'),Path('macro.lef'))


def source_fixture(tmp_path,monkeypatch):
    (tmp_path/'gates.json').write_text(json.dumps(PROFILE['source_gate_receipt']))
    grt=tmp_path/'grt/1-openroad-globalrouting';grt.mkdir(parents=True)
    (grt/'eco_state.json').write_text('{}')
    (grt/'openroad-globalrouting.log').write_text('routing evidence')
    ant=tmp_path/'antenna/1-openroad-checkantennas';ant.mkdir(parents=True)
    (ant/'or_metrics_out.json').write_text(json.dumps({'antenna__violating__nets':0,'antenna__violating__pins':0}))
    monkeypatch.setattr(engine,'validate_overflow',lambda text:None)
    monkeypatch.setattr(engine,'require_live_demand',lambda text:None)
    return grt,ant


def test_completed_screen_can_supply_fresh_eco_state(tmp_path,monkeypatch):
    grt,ant=source_fixture(tmp_path,monkeypatch)
    assert engine.source_checkpoint(tmp_path,PROFILE)==grt/'eco_state.json'


@pytest.mark.parametrize('fault',['receipt','antenna','missing_antenna_metric','missing_state'])
def test_screen_source_refuses_unreviewed_or_incomplete_evidence(tmp_path,monkeypatch,fault):
    grt,ant=source_fixture(tmp_path,monkeypatch)
    if fault=='receipt':(tmp_path/'gates.json').write_text('{}')
    elif fault=='antenna':(ant/'or_metrics_out.json').write_text('{"antenna__violating__nets":1,"antenna__violating__pins":0}')
    elif fault=='missing_antenna_metric':(ant/'or_metrics_out.json').write_text('{}')
    else:(grt/'eco_state.json').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):engine.source_checkpoint(tmp_path,PROFILE)


def test_original_detailed_route_source_still_requires_zero_drc(tmp_path):
    p=tmp_path/'drt/1-openroad-detailedrouting';p.mkdir(parents=True)
    (p/'state_out.json').write_text('{"metrics":{"route__drc_errors":1}}')
    with pytest.raises(ValueError,match='Source DRT incomplete'):engine.source_checkpoint(tmp_path,{})
    (p/'state_out.json').write_text('{"metrics":{"route__drc_errors":0}}')
    assert engine.source_checkpoint(tmp_path,{})==p/'state_out.json'


@pytest.mark.parametrize('global_source,count,okay',[(False,1,True),(False,0,False),(True,0,True),(True,1,False)])
def test_route_reset_receipt_matches_source_kind(global_source,count,okay):
    text=f'TRIPWIRE native route reset: cleared {count} ordinary routed wires'
    if okay:assert engine.validate_route_reset(text,global_source)==count
    else:
        with pytest.raises(ValueError):engine.validate_route_reset(text,global_source)


def test_followup_downloads_only_reviewed_screen_and_never_routes():
    import yaml
    w=yaml.safe_load((Path(__file__).resolve().parents[2]/'.github/workflows/gds-screen-followup.yaml').read_text())
    steps=w['jobs']['harden']['steps']
    d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38347662810
    assert d['with']['name']=='gds-residual-combined-screen-38347662810'
    assert any(s.get('run')=='python workflow-src/scripts/ci/screen_followup.py' for s in steps)
    assert 'OpenROAD.DetailedRouting' not in Path(engine.__file__).read_text()


@pytest.mark.parametrize('fault',['none','signal','clock','empty'])
def test_global_source_tcl_refuses_detailed_signal_or_clock_wires(tmp_path,fault):
    import os
    import subprocess
    helper=Path(__file__).with_name('screen_followup_source.tcl').resolve()
    text='''
namespace eval ord {proc get_db_block {} {return block}}
set nets {signal clock power ground}
set wires [dict create signal NULL clock NULL power wp ground wg]
proc block {method} {return $::nets}
proc net {name method} {
    if {$method eq "getWire"} {return [dict get $::wires $name]}
    if {$method eq "getSigType"} {
        if {$name eq "power"} {return POWER}
        if {$name eq "ground"} {return GROUND}
        if {$name eq "clock"} {return CLOCK}
        return SIGNAL
    }
    error unexpected
}
foreach name $nets {interp alias {} $name {} net $name}
'''
    if fault in ('signal','clock'):text+=f'dict set wires {fault} routed\n'
    if fault=='empty':text+='set nets {power ground}\n'
    text+=f'source {{{helper}}}\nset rc [catch {{tripwire_require_unrouted_screen_source}} message]\nputs "RESULT $rc"\nputs "POWER [dict get $wires power] GROUND [dict get $wires ground]"\n'
    p=tmp_path/'global.tcl';p.write_text(text)
    r=subprocess.run([os.environ.get('TRIPWIRE_TCLSH','tclsh'),str(p)],capture_output=True,text=True)
    assert r.returncode==0
    assert 'RESULT '+('0' if fault=='none' else '1') in r.stdout
    assert 'POWER wp GROUND wg' in r.stdout


def test_followup_wrapper_checks_global_source_before_full_route(tmp_path):
    import os
    import subprocess
    binary=tmp_path/'openroad';binary.write_text('#!/bin/bash\ncat "${@: -1}"\n');binary.chmod(0o755)
    source='source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl'
    script=tmp_path/'grt.tcl';script.write_text('read_current_odb\n'+source+'\nwrite_views\n')
    env=dict(os.environ,PATH=str(tmp_path)+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(tmp_path))
    r=subprocess.run(['bash',str(Path(__file__).with_name('openroad_screen_followup_wrapper.sh')),str(script)],env=env,capture_output=True,text=True)
    assert r.returncode==0 and r.stdout.count(source)==1
    assert r.stdout.index('tripwire_require_unrouted_screen_source')<r.stdout.index(source)
    assert 'tripwire_clear_native_signal_routes' not in r.stdout
