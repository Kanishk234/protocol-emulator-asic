import copy
import json
from pathlib import Path
import pytest
import combined_physical_route as engine
from postant_route import PROFILE
from native_stock_route import CORNERS
from test_post_antenna_fanout import case


@pytest.mark.parametrize('group,key,value',[('run','id',1),('run','head_sha','wrong'),('run','conclusion','failure'),('gates','qualified',False),('gates','minimum_fast_hold_ns',.01),('gates','post_antenna_buffers',4),('gates','post_antenna_connectivity_audited',False)])
def test_exact_successful_source_and_audited_history_required(group,key,value):
    run=copy.deepcopy(PROFILE['run_binding']);gates=copy.deepcopy(PROFILE['gate_receipt'])
    (run if group=='run' else gates)[key]=value
    with pytest.raises(ValueError):engine.validate_provenance(run,gates,PROFILE)


def fixture(tmp_path,monkeypatch):
    before,after,batch=case();proposal={'groups':[],'resizes':[]}
    g=tmp_path/'grt/1-openroad-globalrouting';g.mkdir(parents=True)
    ant=tmp_path/'antenna/1-openroad-checkantennas';ant.mkdir(parents=True)
    odb=g/'chip.odb';odb.write_text('physical view')
    nl=g/'chip.eco.nl.v';nl.write_text(after)
    pnl=g/'chip.eco.pnl.v';pnl.write_text('power view')
    def text(cells):
        return 'COMPONENTS '+str(len(cells))+' ;\n'+'\n'.join(f'- {n} {m} + PLACED ( {i*4800} 241920 ) N ;' for i,(n,m) in enumerate(cells))+'\nEND COMPONENTS'
    from event_nor2_screen import logical_cells
    original=[(n,m) for n,(m,p) in logical_cells(before).items()]
    layout=text(original);changed=text(original+[(g['buffer'],g['master']) for g in batch['groups']])
    d=g/'chip.def';d.write_text(changed)
    sdc=g/'chip.sdc';sdc.write_text('constraints')
    state=dict(odb=str(odb),nl=str(nl),pnl=str(pnl),def_=str(d),sdc=str(sdc));state['def']=state.pop('def_')
    (g/'state_out.json').write_text(json.dumps(state));source=ant/'state_out.json';source.write_text(json.dumps(state))
    (g/'chip.baseline.nl.v').write_text(before);(g/'after_edits.nl.v').write_text(before)
    (g/'postant_0.before.nl.v').write_text(before);(g/'postant_0.after.nl.v').write_text(after);(g/'postant_0.json').write_text(json.dumps(batch))
    (g/'openroad-globalrouting.log').write_text('TRIPWIRE post-antenna fanout: batch 0 added 3 BUF4 cells\nTRIPWIRE post-antenna fanout: converged after 1 batches')
    (tmp_path/'proposal.json').write_text(json.dumps(proposal))
    (ant/'or_metrics_out.json').write_text('{"antenna__violating__nets":0,"antenna__violating__pins":0}')
    t=tmp_path/'timing';t.mkdir();corners={}
    for c in CORNERS:
        metrics={f'timing__setup__ws__corner:{c}':0,f'timing__hold__ws__corner:{c}':.073}
        metrics.update({f'design__max_{kind}_violation__count__corner:{c}':0 for kind in ('slew','fanout','cap')})
        corners[c]={'after':metrics}
    (t/'comparison.json').write_text(json.dumps({'after_state':str(source),'corners':corners}))
    monkeypatch.setattr(engine,'validate_overflow',lambda log:None)
    monkeypatch.setattr(engine,'require_live_demand',lambda log:None)
    profile=dict(PROFILE,validate_change=lambda a,b,p:None)
    return proposal,before,layout,profile,source,g


def test_checkpoint_reaudits_dynamic_history_and_fresh_views(tmp_path,monkeypatch):
    p,b,d,profile,source,g=fixture(tmp_path,monkeypatch)
    assert engine.validate_checkpoint(tmp_path,p,b,d,profile)==source


@pytest.mark.parametrize('fault',['batch_count','stale_nl','electrical','hold','final_wiring'])
def test_checkpoint_refuses_changed_or_unqualified_views(tmp_path,monkeypatch,fault):
    p,b,d,profile,source,g=fixture(tmp_path,monkeypatch)
    if fault=='batch_count':
        profile=copy.deepcopy(profile);profile['gate_receipt']['post_antenna_buffers']=4
    elif fault=='stale_nl':
        state=json.loads(source.read_text());state['nl']=str(g/'chip.baseline.nl.v');source.write_text(json.dumps(state))
    elif fault in ('electrical','hold'):
        path=tmp_path/'timing/comparison.json';t=json.loads(path.read_text());c=CORNERS[0]
        key=f'design__max_fanout_violation__count__corner:{c}' if fault=='electrical' else f'timing__hold__ws__corner:{c}'
        t['corners'][c]['after'][key]=1 if fault=='electrical' else .049;path.write_text(json.dumps(t))
    else:
        path=g/'chip.eco.nl.v';path.write_text(path.read_text().replace('.A(in)','.A(wrong)'))
    with pytest.raises(ValueError):engine.validate_checkpoint(tmp_path,p,b,d,profile)


def test_continuation_downloads_exact_pass_and_does_not_repeat_repairs():
    import yaml
    root=Path(__file__).resolve().parents[2];w=yaml.safe_load((root/'.github/workflows/gds-postant-route.yaml').read_text())
    steps=w['jobs']['harden']['steps'];d=next(s for s in steps if 'download-artifact@' in s.get('uses',''))
    assert d['with']['run-id']==38356513586 and d['with']['name']=='gds-postant-fanout-screen-38356513586'
    assert any(s.get('run')=='python workflow-src/scripts/ci/postant_route.py' for s in steps)
    engine.validate_provenance(PROFILE['run_binding'],PROFILE['gate_receipt'],PROFILE)
    code=(root/'scripts/ci/combined_physical_route.py').read_text()
    assert 'OpenROAD.GlobalRouting' not in code and 'docker' not in code


def test_canonical_replay_tolerates_only_summed_area_roundoff():
    expected={'added_footprint_um2':116.1216,'resize_area_delta_um2':0,'groups':[{'location':[100,200,'N'],'sinks':[['cell','A']]}]}
    actual=copy.deepcopy(expected);actual['added_footprint_um2']=116.12159999999997
    engine.validate_canonical_proposal(actual,expected)
    for fault in ('area','coordinate','sink','nan'):
        changed=copy.deepcopy(actual)
        if fault=='area':changed['added_footprint_um2']+=.001
        elif fault=='coordinate':changed['groups'][0]['location'][0]+=1
        elif fault=='sink':changed['groups'][0]['sinks'][0][1]='B'
        else:changed['added_footprint_um2']=float('nan')
        with pytest.raises(ValueError):engine.validate_canonical_proposal(changed,expected)
