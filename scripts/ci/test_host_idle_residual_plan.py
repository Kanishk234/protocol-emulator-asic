import json
from pathlib import Path
from host_idle_residual_selection import validate_orientations

ROOT = Path(__file__).resolve().parents[2]


def read(name):
    return json.loads((ROOT/'spikes/phase2_stock_flow'/name).read_text())


def test_exact_source_and_two_recorded_edges():
    plan=read('host_idle_residual_plan.json')
    validate_orientations(plan)
    source=read('host_idle_final_checkpoint.json')
    ref=read('host_idle_residual_reference.json')
    assert plan['source_run']==source['run']['id']==ref['source_run']==42305323874
    assert ref['overflow']==2 and len(plan['residual_edges'])==2
    assert all(e['overflow']==1 and e['layer']=='Metal3' for e in plan['residual_edges'])
    assert source['artifact']['id']==13556115899
    assert source['files']['src/signoff.sdc']==read('c_select_final_checkpoint.json')['files']['src/signoff.sdc']


def test_eight_passive_diodes_and_no_logic_sizing_or_clock_edit():
    plan=read('host_idle_residual_plan.json')
    sites=read('host_idle_receiver_site_feasibility.json')
    assert plan['sizing']==[] and not plan.get('clock_reparent')
    assert len(plan['diodes'])==len(plan['allowed_signal_nets_to_reroute'])==8
    assert len({d['name'] for d in plan['diodes']})==8
    for d,s in zip(plan['diodes'][:6],sites['proposals']):
        assert d['locked_site_dbu']==s['diode_location'][:2]
        assert d['locked_orientation']=={'N':'R0','FS':'MX','FN':'MY','S':'R180'}[s['diode_location'][2]]
        assert d['anchor']+'/'+d['pin']==s['target']
        assert d['net'] in plan['allowed_signal_nets_to_reroute']
    assert sites['native_placement_checked'] is False
    assert sites['route_connectivity_checked'] is False


def test_congestion_diodes_force_pin_changes_on_each_reviewed_crossing():
    plan=read('host_idle_residual_plan.json')
    assert plan['congestion_signal_nets']==['net12232','net13408']
    assert [d['net'] for d in plan['diodes'][6:]]==plan['congestion_signal_nets']
    for net,edge in zip(plan['congestion_signal_nets'],plan['residual_edges']):
        assert net in edge['guide_overlap_candidates']
