"""Route the exact qualified final-antenna screen, then stock-constrained RCX/STA."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from cache_gate_functional_audit import validate_stock_constraints
from event_nor2_screen import validate_antenna_only_changes
from native_stock_route import run_step
from official_nov9_preflight import PDK, TOOLS, inventory
from postgrt_timing import CORNERS, screen
from screen_functional_setup import collect
from sram_bank_clean_route import validate_final_route, unique

SOURCE_RUN=44017640255
SOURCE_SHA='e04f800d2ab1701cd97ff801e464830054b2b145'
SOURCE_WORKFLOW='.github/workflows/gds-official-dev4-cache-final-antenna-screen.yaml'
CONFIG_SHA='0b7a388f659ae287b20580fbfa0572b36809df2fd04b63988c5499f3b66598bc'
ODB_SHA='b78055c7400228ff1e7b94808bbd71c490e9587cbd29c83beb1a69c5134ce74e'
RUNNER_ROOT=Path('/home/runner/work/protocol-emulator-asic/protocol-emulator-asic')
SOURCE_STATE=Path('runs/stock-official-baseline/46-openroad-stamidpnr-3/audited_state.json')
ROUTE=Path('runs/cache-final-route')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_metadata(run):
    expected=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path=SOURCE_WORKFLOW)
    if any(run.get(k)!=v for k,v in expected.items()):
        raise ValueError('Wrong exact qualified source run')


def local_view(root, saved):
    root=Path(root).resolve()
    p=Path(saved)
    if p.is_absolute():
        if not p.is_relative_to(RUNNER_ROOT):raise ValueError('Unsafe saved absolute path')
        p=p.relative_to(RUNNER_ROOT)
    if '..' in p.parts:raise ValueError('Unsafe saved relative path')
    p=root/p
    if not p.resolve().is_relative_to(root) or not p.is_file():raise ValueError('Missing/unsafe saved view')
    return p


def timing_pass(comparison):
    for corner in CORNERS:
        for phase in ('before','after'):
            row=comparison['corners'][corner][phase]
            for kind in ('setup','hold'):
                v=row[f'timing__{kind}__ws__corner:{corner}']
                minimum=.05 if corner==CORNERS[0] and kind=='hold' else 0
                if type(v) not in (int,float) or not math.isfinite(v) or v<minimum:return False
                count=row.get(f'timing__{kind}_vio__count__corner:{corner}')
                if type(count) is not int or count!=0:return False
            for kind in ('slew','cap','fanout'):
                if type(row[f'design__max_{kind}_violation__count__corner:{corner}']) is not int or row[f'design__max_{kind}_violation__count__corner:{corner}']!=0:return False
    return True


def inspect_saved(root):
    """Independent read-only inspection; map original runner paths for local review."""
    root=Path(root).resolve()
    receipt=json.loads((root/'compatibility-input.json').read_text())
    if receipt.get('tiles')!='8x4' or receipt.get('tools_sha')!=TOOLS or receipt.get('pdk_revision')!=PDK:
        raise ValueError('Wrong source geometry/toolchain')
    if inventory(root)!=receipt.get('inputs'):raise ValueError('Frozen source/macro inventory changed')
    if digest(root/'src/config.json')!=CONFIG_SHA or receipt['project_config_sha256']!=CONFIG_SHA:
        raise ValueError('Wrong source config hash')
    generated=json.loads((root/'compatibility-generated.json').read_text())
    config=json.loads((root/'src/config_merged.json').read_text())
    if generated.get('generation_passed') is not True or generated['generated_config']!=config:
        raise ValueError('Generated config differs from reviewed screen')
    validate_stock_constraints(config)
    engine=json.loads((root/'compatibility-engine.json').read_text())
    if engine.get('librelane')!='3.1.0.dev4' or engine.get('tools_sha')!=TOOLS or engine.get('pdk_revision')!=PDK:
        raise ValueError('Wrong native source engine')
    import yaml
    info=yaml.safe_load((root/'info.yaml').read_text())['project']
    if (info['tiles']!='8x4' or info['clock_hz']!=50000000 or info['top_module']!='tt_um_tripwire'
            or info['source_files']!=receipt['source_files'] or len(info['source_files'])<=1):
        raise ValueError('Wrong full-design project inputs')
    images=json.loads((root/'compatibility-image.json').read_text())
    if len(images)!=1 or 'ghcr.io/librelane/librelane@sha256:af2405f5d48d8fe14d406ecce913811177a95e365e3b625859677307cace2469' not in images[0]['RepoDigests']:
        raise ValueError('Wrong source container digest')
    if (root/'compatibility-openroad.txt').read_text().strip()!='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0':
        raise ValueError('Wrong source OpenROAD identity')
    audit=root/'runs/stock-corner-audit'
    gates=json.loads((audit/'screen_qualification.json').read_text())
    if (gates.get('qualified') is not True or gates.get('failures')!=[]
            or gates.get('minimum_fast_hold_ns')!=.05 or gates.get('final_global_overflow')!=0
            or gates.get('final_antenna_is_last_physical_step') is not True
            or gates.get('native_repair_congestion_disallowed') is not True
            or gates.get('fresh_netlist_readbacks_verified') is not True
            or gates.get('existing_logic_and_connections_preserved') is not True
            or gates.get('official_gds_signoff') is not False):
        raise ValueError('Source screen is not fully qualified')
    if local_view(root,gates['source_state'])!=root/SOURCE_STATE:
        raise ValueError('Wrong qualified checkpoint')
    state=json.loads((root/SOURCE_STATE).read_text())
    if digest(local_view(root,state['odb']))!=ODB_SHA:raise ValueError('Wrong physical database')
    saved=json.loads((audit/'read_only_audit.json').read_text())
    if saved['source_state']!=gates['source_state']:raise ValueError('Source audit checkpoint mismatch')
    expected={str(SOURCE_STATE),*[state[k] for k in ('odb','def','nl','pnl','sdc')]}
    if set(saved['unchanged_physical_view_hashes'])!=expected:raise ValueError('Incomplete physical view hashes')
    for path,sha in saved['unchanged_physical_view_hashes'].items():
        if digest(local_view(root,path))!=sha:raise ValueError('Physical view hash drift')
    functional=collect(audit)
    if functional!=gates['functional_setup'] or any(r['worst_reported_setup_slack_ns']<=0 for r in functional.values()):
        raise ValueError('Source functional setup guard fails')
    comparison=json.loads((audit/'comparison.json').read_text())
    if not timing_pass(comparison):raise ValueError('Saved ordinary timing/electrical fails')
    for c in CORNERS:
        for phase in ('before','after'):
            raw=json.loads(unique(audit/f'{phase}-{c}','*-openroad-stamidpnr/or_metrics_out.json').read_text())
            for key,v in saved['fresh_corner_metrics'][c].items():
                if raw.get(key)!=v or comparison['corners'][c][phase].get(key)!=v:
                    raise ValueError('Raw saved metric mismatch')
    ant=json.loads(unique(audit/'fresh-antenna','*-openroad-checkantennas/or_metrics_out.json').read_text())
    if any(ant.get(k)!=0 or saved['fresh_antenna_metrics'].get(k)!=0 for k in ('antenna__violating__nets','antenna__violating__pins')):
        raise ValueError('Saved antenna gate fails')
    timing=unique(root/'runs/stock-official-baseline','*-openroad-resizertimingpostgrt/state_out.json')
    old=json.loads(timing.read_text())
    for c in CORNERS:
        for phase in ('before','after'):
            stage=unique(audit/f'{phase}-{c}','*-openroad-stamidpnr')
            if json.loads((stage/'state_in.json').read_text())['odb']!=state['odb']:
                raise ValueError('Readback database mismatch')
            nl=stage/'native_antenna.nl.v';pnl=stage/'native_antenna.pnl.v'
            validate_antenna_only_changes(local_view(root,old['nl']).read_text(),nl.read_text())
            if nl.read_bytes()!=local_view(root,state['nl']).read_bytes() or pnl.read_bytes()!=local_view(root,state['pnl']).read_bytes():
                raise ValueError('Saved fresh netlist readback mismatch')
    return dict(source_run=SOURCE_RUN,source_sha=SOURCE_SHA,source_odb_sha256=ODB_SHA,
                source_config_sha256=CONFIG_SHA,source_state=str(SOURCE_STATE),
                functional_setup=functional,independent_saved_artifact_review=True,
                official_gds_signoff=False)


def verify_source():
    if any(os.environ.get(k) for k in ('LIBRELANE_IMAGE_OVERRIDE','_LLN_OVERRIDE_OPENROAD')) or os.environ.get('TRIPWIRE_NATIVE_RUNTIME','0')!='0':
        raise ValueError('Only the pinned stock Docker runtime is allowed')
    if Path.cwd().resolve()!=RUNNER_ROOT:raise ValueError('Wrong runner path for frozen state')
    validate_metadata(json.loads(Path('official-dev4-source-run.json').read_text()))
    inspect_saved(Path('.'))
    from stock_screen_gate import qualify
    result=qualify(Path('runs/stock-official-baseline'),Path('runs/stock-corner-audit'),
                   require_functional_setup=True,native_final_antenna=True)
    if not result['qualified']:raise ValueError('Independent full screen gate failed')
    return SOURCE_STATE,json.loads(Path('src/config_merged.json').read_text())


def bootstrap(config,source,name):
    """Acquire exact Ciel PDK without physical edits; require fresh antenna0."""
    from physical_runtime import container_flags
    out=Path('runs')/name;out.mkdir(parents=True,exist_ok=False)
    cfg={**config,'meta':{'version':1,'flow':['OpenROAD.CheckAntennas']}}
    path=Path('src/config_'+name+'.json');path.write_text(json.dumps(cfg,indent=2)+'\n')
    subprocess.run([sys.executable,'-m','librelane','--pdk-root','/home/runner/pdk',*container_flags(),
                    '--pdk','ihp-sg13cmos5l','--run-tag',name,'--force-run-dir',str(out),
                    '--hide-progress-bar','--with-initial-state',str(source),str(path)],check=True)
    resolved=json.loads((out/'resolved.json').read_text());pdk=Path(resolved['PDK_ROOT'])
    if pdk.name!=PDK or not (pdk/'ihp-sg13cmos5l').is_dir():raise ValueError('Wrong exact Ciel PDK')
    os.environ['PDK_ROOT']=str(pdk)
    ant=json.loads(unique(out,'*-openroad-checkantennas/or_metrics_out.json').read_text())
    if any(ant.get(k)!=0 for k in ('antenna__violating__nets','antenna__violating__pins')):
        raise ValueError('Fresh source antenna check fails')
    return str(pdk)


def prepare():
    source,config=verify_source()
    pdk=bootstrap(config,source,'cache-final-route-pdk')
    out=Path('runs/cache-final-pre-route-timing')
    screen(Path('src/config_merged.json'),source,out,pdk,repaired=source,
           extra_tcl=Path('scripts/ci/functional_setup_frontier.tcl'),sta_grt_adjustment=config['GRT_ADJUSTMENT'])
    functional=collect(out);comparison=json.loads((out/'comparison.json').read_text())
    expected=json.loads(Path('runs/stock-corner-audit/screen_qualification.json').read_text())['functional_setup']
    ready=timing_pass(comparison) and all(r['worst_reported_setup_slack_ns']>0
            and r['endpoint_inventory']==expected[c]['endpoint_inventory'] for c,r in functional.items())
    result=dict(qualified=ready,source_run=SOURCE_RUN,source_sha=SOURCE_SHA,source_odb_sha256=ODB_SHA,
                functional_setup=functional,resolved_pdk_root=pdk,minimum_fast_hold_ns=.05,
                stock_uncertainty_ns=.25,workflow_run_id=os.environ.get('GITHUB_RUN_ID'),official_gds_signoff=False)
    Path('runs/cache-final-pre-route-gates.json').write_text(json.dumps(result,indent=2)+'\n')
    if not ready:raise ValueError('Fresh source timing/electrical gates fail; DRT refused')


def restore_pdk(receipt):
    pdk=Path(receipt['resolved_pdk_root'])
    if pdk.name!=PDK or not (pdk/'ihp-sg13cmos5l').is_dir():raise ValueError('Missing exact PDK')
    os.environ['PDK_ROOT']=str(pdk)


def route():
    source,config=verify_source()
    row=json.loads(Path('runs/cache-final-pre-route-gates.json').read_text())
    if row.get('qualified') is not True or row.get('source_run')!=SOURCE_RUN or row.get('source_odb_sha256')!=ODB_SHA or row.get('source_sha')!=SOURCE_SHA or row.get('workflow_run_id')!=os.environ.get('GITHUB_RUN_ID'):
        raise ValueError('No qualified fresh pre-route gates')
    restore_pdk(row)
    run_step(config,source,ROUTE,['OpenROAD.DetailedRouting'])
    state_path=unique(ROUTE,'*-openroad-detailedrouting/state_out.json')
    state=json.loads(state_path.read_text())
    raw=json.loads((state_path.parent/'or_metrics_out.json').read_text())
    if any(type(v) is not int or v!=0 for v in (state.get('metrics',{}).get('route__drc_errors'),raw.get('route__drc_errors'))):
        raise ValueError('Completed detailed route must have fresh DRC0')
    validate_final_route(source,ROUTE)
    receipt=dict(completed=True,source_run=SOURCE_RUN,source_sha=SOURCE_SHA,source_odb_sha256=ODB_SHA,
                 workflow_run_id=os.environ.get('GITHUB_RUN_ID'),route_drc_errors=0,
                 routed_odb_sha256=digest(state['odb']),routed_nl_sha256=digest(state['nl']),
                 extracted_timing_performed=False,official_gds_signoff=False)
    (ROUTE/'route_completion.json').write_text(json.dumps(receipt,indent=2)+'\n')


def extracted_failures(summary,functional,electrical,antenna,expected_endpoints=None):
    failures=[]
    if set(functional)!=set(CORNERS):return ['Missing extracted functional setup corners']
    for c in CORNERS:
        if expected_endpoints is not None and functional[c].get('endpoint_inventory')!=expected_endpoints.get(c):
            failures.append(f'{c} extracted endpoint inventory changed')
        for kind in ('setup','hold'):
            v=summary.get(f'timing__{kind}__ws__corner:{c}')
            minimum=.05 if c==CORNERS[0] and kind=='hold' else 0
            if type(v) not in (int,float) or not math.isfinite(v) or v<minimum:
                failures.append(f'{c} {kind}: {v} < {minimum}')
            count=summary.get(f'timing__{kind}_vio__count__corner:{c}')
            if type(count) is not int or count!=0:failures.append(f'{c} {kind} violation count: {count}')
        v=functional[c].get('worst_reported_setup_slack_ns')
        if type(v) not in (int,float) or not math.isfinite(v) or v<=0:failures.append(f'{c} functional setup must be positive: {v}')
    if set(electrical)!=set(CORNERS) or any(r.get('no_reported_electrical_violations') is not True for r in electrical.values()):
        failures.append('Extracted electrical checks incomplete/nonzero')
    if any(type(antenna.get(k)) is not int or antenna.get(k)!=0 for k in ('antenna__violating__nets','antenna__violating__pins')):failures.append('Extracted antenna nonzero/missing')
    return failures


def extract():
    source,config=verify_source()
    row=json.loads((ROUTE/'route_completion.json').read_text())
    state_path=unique(ROUTE,'*-openroad-detailedrouting/state_out.json');state=json.loads(state_path.read_text())
    if (row.get('completed') is not True or row.get('source_run')!=SOURCE_RUN or row.get('source_sha')!=SOURCE_SHA or row.get('source_odb_sha256')!=ODB_SHA
            or row.get('workflow_run_id')!=os.environ.get('GITHUB_RUN_ID') or row.get('route_drc_errors')!=0
            or digest(state['odb'])!=row.get('routed_odb_sha256') or digest(state['nl'])!=row.get('routed_nl_sha256')):
        raise ValueError('Wrong/incomplete routed artifact')
    bootstrap(config,source,'cache-final-extract-pdk')
    from extracted_timing import main as run_extract
    run_extract(ROUTE,stock_constraints=True,functional_setup=True)
    root=Path('runs/extracted-timing')
    summary=json.loads((root/'corner_summary.json').read_text())
    functional=json.loads((root/'functional_setup.json').read_text())
    electrical=json.loads((root/'electrical_summary.json').read_text())
    antenna=json.loads(unique(root,'*-openroad-checkantennas/or_metrics_out.json').read_text())
    expected=json.loads(Path('runs/stock-corner-audit/screen_qualification.json').read_text())['functional_setup']
    failures=extracted_failures(summary,functional,electrical,antenna,{c:r['endpoint_inventory'] for c,r in expected.items()})
    result=dict(qualified=not failures,source_run=SOURCE_RUN,source_sha=SOURCE_SHA,route_state=str(state_path),
                extracted_timing=summary,functional_setup=functional,electrical=electrical,antenna=antenna,
                stock_uncertainty_ns=.25,failures=failures,routed_protocol_replay_performed=False,official_gds_signoff=False)
    Path('runs/cache-final-extracted-gates.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if failures:raise ValueError('Extracted timing/electrical/antenna gates fail')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('prepare','route','extract'))
    globals()[parser.parse_args().stage]()
