"""Exact qualified combined screen continuation through DRT and extraction."""
import hashlib
import json
import math
import os
from pathlib import Path
from combined_physical_plan import plan,validate_change
from combined_physical_screen import validate_placements
from electrical_incremental_route import continue_route
from event_nor2_screen import logical_cells,validate_antenna_only_changes,validate_overflow
from incremental_repair_audit import require_live_demand
from native_stock_route import fingerprints,qualified,validate_source
from sram_bank_clean_route import unique
from sram_bank_clean_screen import configure,electrical_clean
from sram_bank_plan import MACRO_LEF_SHA,plan as bank_plan

SOURCE_RUN=38334245126
SOURCE_SHA='08d9279b0f0ec3718cbcc5c36dc1529415013de9'


def validate_provenance(run,gates,profile=None):
    if profile is not None:
        if profile['gate_receipt'].get('qualified') is not True or profile['gate_receipt'].get('minimum_fast_hold_ns')!=.05:
            raise ValueError('Unqualified physical source profile')
        if any(run.get(k)!=v for k,v in profile['run_binding'].items()) or gates!=profile['gate_receipt']:
            raise ValueError('Wrong qualified physical source or strict gate receipt')
        return
    expected=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-combined-physical-screen.yaml')
    if any(run.get(k)!=v for k,v in expected.items()):raise ValueError('Wrong qualified combined source')
    expected=dict(source_run=38305592967,qualified=True,added_buffers=76,resized_cells=8,
        minimum_fast_hold_ns=.05,all_original_connections_audited=True,source_detailed_wires_cleared=True,
        full_reroute=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    if gates!=expected:raise ValueError('Wrong combined strict qualification')


def validate_canonical_proposal(saved,expected):
    canonical=json.loads(json.dumps(expected));actual=json.loads(json.dumps(saved))
    for key in ('added_footprint_um2','resize_area_delta_um2'):
        if key not in canonical:continue
        value=actual.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or abs(value-canonical[key])>1e-9:
            raise ValueError('Wrong canonical combined area')
        actual[key]=canonical[key]
    if actual!=canonical:raise ValueError('Wrong canonical combined proposal')


def validate_checkpoint(root,proposal,baseline,layout,profile=None):
    profile={} if profile is None else profile
    validate_canonical_proposal(json.loads((root/'proposal.json').read_text()),proposal)
    timing=json.loads((root/'timing/comparison.json').read_text())
    source=unique(root/'antenna','*-openroad-checkantennas/state_out.json')
    if Path(timing['after_state']).resolve()!=source.resolve():raise ValueError('Wrong measured combined checkpoint')
    antenna=json.loads((source.parent/'or_metrics_out.json').read_text())
    if not qualified(timing,antenna) or not electrical_clean(timing):raise ValueError('Saved combined strict gates fail')
    raw=unique(root/'grt','*-openroad-globalrouting/state_out.json');state=json.loads(source.read_text());odb=Path(state['odb'])
    if odb.resolve()!=Path(json.loads(raw.read_text())['odb']).resolve():raise ValueError('Wrong combined ODB')
    for k in ('odb','def','nl','pnl','sdc'):
        if not Path(state[k]).is_file():raise ValueError('Missing combined view '+k)
    for k in ('nl','pnl'):
        if Path(state[k]).resolve()!=odb.with_suffix('.eco.'+k+'.v').resolve():raise ValueError('Stale combined '+k)
    before=odb.with_suffix('.baseline.nl.v').read_text();edited=(raw.parent/'after_edits.nl.v').read_text()
    if logical_cells(before)!=logical_cells(baseline):raise ValueError('Combined source mismatch')
    profile.get('validate_change',validate_change)(before,edited,proposal)
    log=(raw.parent/'openroad-globalrouting.log').read_text()
    if 'post_antenna_audit' in profile:
        result=profile['post_antenna_audit'](edited,Path(state['nl']).read_text(),raw.parent,log)
        if any(profile['gate_receipt'].get(k)!=v for k,v in result.items()):raise ValueError('Wrong post-antenna repair audit receipt')
    else:validate_antenna_only_changes(edited,Path(state['nl']).read_text())
    validate_placements(layout,Path(state['def']).read_text(),proposal)
    log=(raw.parent/'openroad-globalrouting.log').read_text();validate_overflow(log);require_live_demand(log)
    return source


def main(profile=None):
    profile={} if profile is None else profile
    root=Path(profile.get('screen_root','runs/combined-physical-screen'))
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),json.loads((root/'gates.json').read_text()),profile if profile else None)
    original=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),json.loads(Path('/tmp/native-trusted-files.json').read_text()),fingerprints(Path.cwd()),profile='clock8')
    macro=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macro)!=1 or len(std)!=1:raise ValueError('Missing pinned combined geometry')
    ref=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((ref/'tt_um_tripwire.nl.v').read_text(),(ref/'tt_um_tripwire.def').read_text(),std[0],macro[0],clean_postgpl=True)
    config=configure(json.loads(Path('/tmp/native-trusted-config.json').read_text()),bank,electrical=True)
    if config!=json.loads(Path(profile.get('recipe_path','src/config_combined_physical_screen.json')).read_text()):raise ValueError('Wrong complete combined recipe')
    baseline=Path(profile.get('baseline_nl','runs/electrical-incremental-route/drt/1-openroad-detailedrouting/tt_um_tripwire.nl.v')).read_text()
    layout=Path(profile.get('baseline_def','runs/electrical-incremental-route/drt/1-openroad-detailedrouting/tt_um_tripwire.def')).read_text()
    sta=Path(profile['timing_root']) if 'timing_root' in profile else unique(Path('runs/extracted-timing'),'*openroad-stapostpnr/state_out.json').parent
    fmt=profile.get('timing_corner_format','{corner}')
    proposal=profile.get('plan',plan)(baseline,layout,(sta/fmt.format(corner='nom_fast_1p32V_m40C')/'min.rpt').read_text(),
        {c:(sta/fmt.format(corner=c)/'checks.rpt').read_text() for c in ('nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C')},std[0],macro[0])
    source=validate_checkpoint(root,proposal,baseline,layout,profile)
    # Keep original extracted evidence, make fresh output available to the
    # existing zero-DRC extraction helper. No repair or full GRT repeated.
    output=Path(profile.get('output_root','runs/combined-physical-route'))
    if Path('runs/extracted-timing').exists():Path('runs/extracted-timing').rename(Path(profile.get('saved_extraction_root','runs/combined-source-extracted-timing')))
    continue_route(config,source,output,source_run=profile.get('source_run',SOURCE_RUN))


if __name__=='__main__':main()
