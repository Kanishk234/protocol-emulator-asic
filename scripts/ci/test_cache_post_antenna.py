import hashlib
import json
from pathlib import Path
import subprocess

import pytest
import yaml

import cache_post_antenna as trial
from postgrt_timing import CORNERS

ROOT=Path(__file__).resolve().parents[2]
GATE='sg13cmos5l_nand2_2 cell0 (.A(a), .B(b), .Y(y));\n'
DIODE='sg13cmos5l_antennanp diode0 (.A(y));\n'


def fixture(tmp_path):
    physical=tmp_path/'physical'
    audit=tmp_path/'audit'
    timing=physical/'44-openroad-resizertimingpostgrt'
    ant=physical/'45-openroad-repairantennas-1'
    route=physical/'46-openroad-globalrouting-1'
    sta=physical/'47-openroad-stamidpnr-3'
    child=ant/'1-openroad-diodeinsertion'
    for p in (timing,child,route,sta):p.mkdir(parents=True)
    old={k:str(timing/('chip.'+k)) for k in ('odb','def','nl','pnl','sdc')}
    for k,p in old.items():Path(p).write_text(GATE if k in ('nl','pnl') else k)
    (timing/'state_out.json').write_text(json.dumps(old))
    (ant/'state_in.json').write_text(json.dumps(old))
    final={**old,'odb':str(child/'chip.odb'),'def':str(child/'chip.def')}
    Path(final['odb']).write_text('repaired database')
    Path(final['def']).write_text('repaired placement')
    (ant/'state_out.json').write_text(json.dumps(final))
    (route/'state_in.json').write_text(json.dumps(final))
    final={**final,'odb':str(route/'chip.odb'),'def':str(route/'chip.def')}
    Path(final['odb']).write_text('final routed database')
    Path(final['def']).write_text('final routes')
    (route/'state_out.json').write_text(json.dumps(final))
    (route/'openroad-globalrouting-1.log').write_text('+ global_route -congestion_iterations 50\nTotal 100 80 80.00% 0 / 0 / 0\n')
    source=sta/'state_out.json'
    source.write_text(json.dumps(final))
    (physical/'resolved.json').write_text(json.dumps({'GRT_ALLOW_CONGESTION':False}))
    (child/'openroad-diodeinsertion.log').write_text('+ repair_antennas sg13cmos5l_antennanp -iterations 3 -ratio_margin 10 -diode_only\n')
    for c in CORNERS:
        for phase in ('before','after'):
            p=audit/f'{phase}-{c}'/'1-openroad-stamidpnr';p.mkdir(parents=True)
            (p/'state_in.json').write_text(json.dumps(final))
            for name in ('nl','pnl'):(p/f'native_antenna.{name}.v').write_text(GATE+DIODE)
    return physical,source,audit


def test_fresh_exports_preserve_original_state_and_only_add_diodes(tmp_path):
    physical,source,audit=fixture(tmp_path)
    before=source.read_bytes()
    final=trial.promote(physical,source,audit)
    assert source.read_bytes()==before
    result=trial.validate_final(physical,final,audit)
    assert result['fresh_netlist_readbacks_verified']
    assert result['native_repair_congestion_disallowed']
    state=json.loads(final.read_text())
    assert Path(state['nl']).read_text()==GATE+DIODE
    assert state['metrics']=={} and state['spef'] is None


@pytest.mark.parametrize('case',['logic','diode_net','missing','readback_odb','command','congestion','chain','pnl_repeat'])
def test_stale_or_unsafe_post_repair_evidence_fails_closed(tmp_path,case):
    physical,source,audit=fixture(tmp_path)
    p=audit/f'after-{CORNERS[0]}'/'1-openroad-stamidpnr'
    if case=='logic':(p/'native_antenna.nl.v').write_text(GATE.replace('.B(b)','.B(a)')+DIODE)
    if case=='diode_net':(p/'native_antenna.nl.v').write_text(GATE+DIODE.replace('.A(y)','.A(new_net)'))
    if case=='missing':(p/'native_antenna.nl.v').unlink()
    if case=='readback_odb':(p/'state_in.json').write_text('{"odb":"wrong.odb"}')
    if case=='pnl_repeat':(p/'native_antenna.pnl.v').write_text('different powered view')
    if case=='congestion':(physical/'resolved.json').write_text('{"GRT_ALLOW_CONGESTION":true}')
    if case=='command':
        p=physical/'45-openroad-repairantennas-1/1-openroad-diodeinsertion/openroad-diodeinsertion.log'
        p.write_text(p.read_text().rstrip()+' -allow_congestion\n')
    if case=='chain':(physical/'45-openroad-repairantennas-1/state_in.json').write_text('{"odb":"wrong.odb"}')
    with pytest.raises(ValueError):trial.promote(physical,source,audit)


def test_declared_config_is_exactly_native_insertion_plus_no_congestion(tmp_path,monkeypatch):
    (tmp_path/'src').mkdir()
    path=tmp_path/'src/config.json'
    before={'CLOCK_PERIOD':20,'GRT_ALLOW_CONGESTION':True}
    path.write_text(json.dumps(before))
    monkeypatch.setattr(trial,'BASE_SHA',hashlib.sha256(path.read_bytes()).hexdigest())
    selected=tmp_path/'spikes/phase2_stock_flow/selected_profile.json'
    selected.parent.mkdir(parents=True)
    selected.write_text(json.dumps({'profile':'portable_cache_no_a22oi','changes':{}}))
    receipt=trial.prepare(tmp_path)
    after=json.loads(path.read_text())
    assert after=={**before,'GRT_ALLOW_CONGESTION':False,'meta':{'version':1,'flow':'Classic','substituting_steps':trial.SUBSTITUTIONS}}
    assert not receipt['physical_qualified']
    with pytest.raises(ValueError):trial.prepare(tmp_path)


def test_workflow_retains_strict_setup_and_all_native_physical_steps():
    p=ROOT/'.github/workflows/gds-official-dev4-cache-post-antenna-screen.yaml'
    w=yaml.safe_load(p.read_text());assert w['on']=={'workflow_dispatch':{}}
    steps=w['jobs']['screen']['steps']
    gate=next(s['run'] for s in steps if s['name']=='Require all final screening gates')
    assert '--require-functional-setup' in gate and '--native-post-antenna' in gate
    text='\n'.join(s.get('run','') for s in steps)
    assert '--to OpenROAD.STAMidPNR-3' in text
    assert "actual==original[:i+1]+['OpenROAD.RepairAntennas-1','OpenROAD.GlobalRouting-1']+original[i+1:]" in text
    for s in steps:
        if 'run' in s:subprocess.run(['bash','-n'],input=s['run'],text=True,check=True)
    evidence=json.loads((ROOT/'spikes/phase2_stock_flow/cache_post_antenna/candidate.json').read_text())
    from official_nov9_preflight import CONFIGS
    assert evidence['candidate_config_sha256'] in CONFIGS


@pytest.mark.parametrize('overflow,break_chain,passes',[(0,False,True),(1,False,False),(0,True,None)])
def test_final_gate_uses_actual_last_route_and_all_original_checks(tmp_path,overflow,break_chain,passes):
    from test_stock_screen_gate import fixture as raw_fixture
    from stock_screen_gate import qualify
    physical,source,audit=fixture(tmp_path)
    raw_root=tmp_path/'raw';raw_root.mkdir()
    _,raw=raw_fixture(raw_root)
    import shutil
    for p in raw.rglob('*'):
        if p.is_file():
            target=audit/p.relative_to(raw);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    # All raw metrics are zero/positive, while actual report margin is separately positive.
    for c in CORNERS:
        for phase in ('before','after'):
            d=audit/f'{phase}-{c}'/'1-openroad-stamidpnr'
            (d/'functional_setup_frontier.rpt').write_text(f'TRIPWIRE_FUNCTIONAL_SETUP {c}\nFLOP_DATA_ENDPOINTS 2418\nOUTPUT_ENDPOINTS 24\n2.0 slack (MET)\n')
            for name in ('max.rpt','min.rpt'):(d/name).write_text('0.250 19.750 clock uncertainty\n')
    promoted=trial.promote(physical,source,audit)
    receipt=json.loads((audit/'read_only_audit.json').read_text())
    state=json.loads(promoted.read_text());paths=[promoted]+[Path(state[k]) for k in ('odb','def','nl','pnl','sdc')]
    receipt.update(source_state=str(promoted),unchanged_physical_view_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (audit/'read_only_audit.json').write_text(json.dumps(receipt))
    log=physical/'46-openroad-globalrouting-1/openroad-globalrouting-1.log'
    log.write_text(log.read_text().replace('0 / 0 / 0',f'0 / 0 / {overflow}'))
    if break_chain:
        (physical/'46-openroad-globalrouting-1/state_in.json').write_text('{"odb":"wrong"}')
        with pytest.raises(ValueError):qualify(physical,audit,require_functional_setup=True,native_post_antenna=True)
    else:
        result=qualify(physical,audit,require_functional_setup=True,native_post_antenna=True)
        assert result['qualified'] is passes
        assert result['final_global_overflow']==overflow
