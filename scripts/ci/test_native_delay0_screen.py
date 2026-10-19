from pathlib import Path
from typing import get_args
import pytest
from native_delay0_screen import configure
from native_wire150_screen import configure as wire_configure
from native_stock_screen import configure as base_configure


def test_mapping_trial_changes_only_native_synthesis_strategy():
    source=base_configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),'AREA 1',
        Path('src/signoff.sdc'),hold_target=.10,clock_cluster=8)
    before=wire_configure(source);after=configure(source)
    assert {k for k in before if before[k]!=after[k]}=={'SYNTH_STRATEGY'}
    assert after['SYNTH_STRATEGY']=='DELAY 0'
    assert after['GRT_RESIZER_SETUP_SLACK_MARGIN']==0
    assert after['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125
    assert after['CLOCK_PERIOD']==20 and before['SYNTH_STRATEGY']=='AREA 1'


def test_actual_workflow_preflight_accepts_pinned_mapping_schema():
    pytest.importorskip('librelane')
    import yaml
    from librelane.steps import Step
    variable=next(v for v in Step.factory.get('Yosys.Synthesis').config_vars if v.name=='SYNTH_STRATEGY')
    assert 'DELAY 0' in get_args(variable.type)
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-delay0-setup-reserve-screen.yaml'
    steps=yaml.safe_load(p.read_text())['jobs']['harden']['steps']
    step=next(s for s in steps if s['name']=='Verify the pinned declarative insertion and stop point')
    code=step['run'].split("python - <<'PY'\n",1)[1].rsplit('\nPY',1)[0]
    exec(compile(code,str(p),'exec'),{})


def test_workflow_labels_actual_delay_mapping_and_retains_guard_evidence():
    import yaml
    p=Path(__file__).resolve().parents[2]/'.github/workflows/gds-native-delay0-setup-reserve-screen.yaml'
    w=yaml.safe_load(p.read_text());job=w['jobs']['harden'];steps=job['steps']
    assert 'strategy' not in job
    commands='\n'.join(s.get('run','') for s in steps)
    assert 'native_delay0_screen.py' in commands
    assert 'DELAY 0' in commands
    early=next(s for s in steps if s['name']=='Upload early gate evidence')['with']['path']
    assert 'capture_setup.rpt' in early and 'yosys-synthesis/config.json' in early
    artifact=next(s for s in steps if s['name']=='Upload matched screen evidence')['with']['name']
    assert artifact=='gds-native-delay0-setup-reserve-${{ github.run_id }}'
