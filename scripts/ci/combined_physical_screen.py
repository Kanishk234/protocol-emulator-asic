"""Strict combined repair screen; no detailed-routing step or signoff claim."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from combined_physical_plan import plan,target_call,validate_change
from event_nor2_screen import logical_cells,validate_antenna_only_changes,validate_overflow
from extracted_sizing_sensitivity import validate_run
from incremental_repair_audit import placements,require_live_demand
from native_stock_route import fingerprints,qualified,run_step,validate_source
from postgrt_timing import screen
from sram_bank_clean_route import unique
from sram_bank_clean_screen import configure,electrical_clean
from sram_bank_plan import MACRO_LEF_SHA,plan as bank_plan


def validate_placements(layout,changed,proposal):
    old,new=placements(layout),placements(changed)
    expected=dict(old)
    for r in proposal['resizes']:
        expected[r['instance']]=(r['new_master'],*r['location'])
    if any(new.get(n)!=v for n,v in expected.items()):raise ValueError('Unreviewed original cell movement/master change')
    if not {g['buffer'] for g in proposal['groups']}<=set(new):raise ValueError('Missing proposed buffers')


def source_checkpoint(root,profile):
    if profile.get('source_kind','detailed-route')=='detailed-route':
        source=unique(root/'drt','*-openroad-detailedrouting/state_out.json')
        if json.loads(source.read_text())['metrics'].get('route__drc_errors')!=0:
            raise ValueError('Source DRT incomplete')
        return source
    if profile.get('source_kind')!='global-screen':raise ValueError('Unreviewed source kind')
    receipt=json.loads((root/'gates.json').read_text())
    if receipt!=profile['source_gate_receipt']:raise ValueError('Wrong source screen gate receipt')
    previous=unique(root/'grt','*-openroad-globalrouting/openroad-globalrouting.log')
    text=previous.read_text();validate_overflow(text);require_live_demand(text)
    checked=unique(root/'antenna','*-openroad-checkantennas/or_metrics_out.json')
    antenna=json.loads(checked.read_text())
    if antenna.get('antenna__violating__nets')!=0 or antenna.get('antenna__violating__pins')!=0:
        raise ValueError('Source screen antenna gate failed')
    return unique(root/'grt','*-openroad-globalrouting/eco_state.json')


def validate_route_reset(log,global_source=False):
    resets=re.findall(r'TRIPWIRE native route reset: cleared (\d+) ordinary routed wires',log)
    if len(resets)!=1 or (int(resets[0])!=0 if global_source else int(resets[0])<=0):
        raise ValueError('Wrong source detailed-wire cleanup receipt')
    return int(resets[0])


def main(profile=None):
    profile={} if profile is None else profile
    build=profile.get('plan',plan);emit=profile.get('target_call',target_call);conserve=profile.get('validate_change',validate_change)
    validate_run(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),profile.get('run_binding'))
    root=Path(profile.get('route_root','runs/electrical-incremental-route'))
    source=source_checkpoint(root,profile);state=json.loads(source.read_text())
    for k in ('nl','pnl','odb','def','sdc'):
        if not Path(state[k]).is_file():raise ValueError('Missing routed source '+k)
    trusted=json.loads(Path('/tmp/native-trusted-config.json').read_text())
    original=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),json.loads(Path('/tmp/native-trusted-files.json').read_text()),fingerprints(Path.cwd()),profile='clock8')
    macro=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macro)!=1 or len(std)!=1:raise ValueError('Missing pinned geometry')
    ref=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((ref/'tt_um_tripwire.nl.v').read_text(),(ref/'tt_um_tripwire.def').read_text(),std[0],macro[0],clean_postgpl=True)
    config=configure(trusted,bank,electrical=True)
    if config!=json.loads(Path(profile.get('recipe_path','src/config_electrical_incremental_route.json')).read_text()):raise ValueError('Wrong complete physical recipe')
    sta=Path(profile['timing_root']) if 'timing_root' in profile else unique(Path('runs/extracted-timing'),'*openroad-stapostpnr/state_out.json').parent
    baseline=Path(state['nl']).read_text();layout=Path(state['def']).read_text()
    proposal=build(baseline,layout,(sta/profile.get('timing_corner_format','{corner}').format(corner='nom_fast_1p32V_m40C')/'min.rpt').read_text(),
        {c:(sta/profile.get('timing_corner_format','{corner}').format(corner=c)/'checks.rpt').read_text() for c in ('nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C')},std[0],macro[0])
    target=Path('workflow-src/scripts/ci/combined_physical_targets.tcl')
    if target.exists():raise ValueError('Repeated combined repair')
    target.write_text(emit(layout,proposal))
    output=Path(profile.get('output_root','runs/combined-physical-screen'));output.mkdir(exist_ok=False)
    (output/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    subprocess.run(['docker','build','-t',profile.get('image','tripwire-combined-screen:local'),'-f',profile.get('dockerfile','workflow-src/scripts/ci/Dockerfile.openroad-combined-screen'),'workflow-src/scripts/ci'],check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE']=profile.get('image','tripwire-combined-screen:local')
    # Discard obsolete extraction outputs from the old physical database.
    clean=dict(state,spef=None,sdf=None,lib=None,metrics={})
    initial=output/'source_state.json';initial.write_text(json.dumps(clean,indent=2)+'\n')
    run_step(config,initial,output/'grt',['OpenROAD.GlobalRouting'])
    raw=unique(output/'grt','*-openroad-globalrouting/state_out.json');final=json.loads(raw.read_text());odb=Path(final['odb'])
    before=odb.with_suffix('.baseline.nl.v').read_text();edited=(raw.parent/'after_edits.nl.v').read_text();nl=odb.with_suffix('.eco.nl.v');pnl=odb.with_suffix('.eco.pnl.v')
    if logical_cells(before)!=logical_cells(baseline):raise ValueError('Physical ODB input disagrees with source NL')
    conserve(before,edited,proposal)
    postant={}
    if 'post_antenna_audit' in profile:
        postant=profile['post_antenna_audit'](edited,nl.read_text(),raw.parent,(raw.parent/'openroad-globalrouting.log').read_text())
    else:validate_antenna_only_changes(edited,nl.read_text())
    validate_placements(layout,Path(final['def']).read_text(),proposal)
    log=(raw.parent/'openroad-globalrouting.log').read_text();validate_overflow(log);require_live_demand(log)
    reset_count=validate_route_reset(log,profile.get('source_kind')=='global-screen')
    final.update(nl=str(nl.resolve()),pnl=str(pnl.resolve()),spef=None,sdf=None,lib=None)
    changed=raw.with_name('eco_state.json');changed.write_text(json.dumps(final,indent=2)+'\n')
    run_step(config,changed,output/'antenna',['OpenROAD.CheckAntennas'])
    checked=unique(output/'antenna','*-openroad-checkantennas/state_out.json');antenna=json.loads((checked.parent/'or_metrics_out.json').read_text())
    path=Path(profile.get('screen_config','src/config_combined_physical_screen.json'));path.write_text(json.dumps(config,indent=2)+'\n')
    extra={'extra_tcl':Path(profile['electrical_margin_tcl'])} if profile.get('electrical_margin_tcl') else {}
    screen(path,source,output/'timing',os.environ['PDK_ROOT'],repaired=checked,sdc=Path('src/signoff.sdc'),**extra)
    timing=json.loads((output/'timing/comparison.json').read_text())
    ready=qualified(timing,antenna) and electrical_clean(timing)
    receipt=dict(source_run=profile.get('source_run',38305592967),qualified=ready,
        added_buffers=proposal['added_buffers'],resized_cells=len(proposal['resizes']),minimum_fast_hold_ns=.05,
        all_original_connections_audited=True,source_detailed_wires_cleared=reset_count>0,
        full_reroute=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    if profile.get('source_kind')=='global-screen':
        receipt.update(source_global_screen=True,source_detailed_wire_reset_count=reset_count)
    receipt.update(postant)
    (output/'gates.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if not ready:raise ValueError('Combined physical screen fails timing/electrical/antenna gates; no DRT')


if __name__=='__main__':main()
