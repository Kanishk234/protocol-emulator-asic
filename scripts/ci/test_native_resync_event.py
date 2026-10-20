from pathlib import Path
import pytest
import native_resync_event_screen as target
import native_stock_screen


def test_entrypoint_requires_exact_combo_and_uses_unchanged_physical_policy(monkeypatch):
    calls=[]
    monkeypatch.setattr(target,'reserve_screen',lambda **kw:calls.append(kw))
    for variant in ('unknown','bs-resync','bs-event-late'):
        monkeypatch.setenv('VARIANT',variant)
        with pytest.raises(ValueError):target.main()
    monkeypatch.setenv('VARIANT','bs-resync-event');target.main()
    assert calls==[{'config_transform':target.configure}]
    cfg=target.configure(native_stock_screen.configure(dict(CLOCK_PERIOD=20,PL_TARGET_DENSITY_PCT=56),
        'AREA 1',Path('src/signoff.sdc'),hold_target=.10,clock_cluster=8))
    assert cfg['SYNTH_STRATEGY']=='AREA 1' and cfg['GRT_RESIZER_SETUP_SLACK_MARGIN']==0
    assert cfg['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH']==150 and cfg['GRT_RESIZER_HOLD_SLACK_MARGIN']==.125


def test_native_runner_rejects_unreviewed_hardware(monkeypatch):
    monkeypatch.setenv('VARIANT','unreviewed')
    with pytest.raises(ValueError):native_stock_screen.main()


def test_workflow_applies_existing_verified_patch_and_keeps_headroom_gate():
    import yaml
    root=Path(__file__).resolve().parents[2]
    path=root/'.github/workflows/gds-native-resync-event-setup-reserve-screen.yaml'
    job=yaml.safe_load(path.read_text())['jobs']['harden']
    assert job['env']['VARIANT']=='bs-resync-event'
    commands='\n'.join(s.get('run','') for s in job['steps'])
    assert 'native_resync_event_screen.py' in commands
    assert 'timing_trial.py' in commands
    assert job['env']['CANDIDATE_SHA']=='3393eea9a58c5cad9077cc360a8515d0e5ec8284'
    assert (root/'spikes/r4_floorplan/bs_resync_event.patch').is_file()
