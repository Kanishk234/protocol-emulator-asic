"""Exact qualified combined screen continuation through DRT and extraction."""
import hashlib
import json
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


def validate_provenance(run,gates):
    expected=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',path='.github/workflows/gds-combined-physical-screen.yaml')
    if any(run.get(k)!=v for k,v in expected.items()):raise ValueError('Wrong qualified combined source')
    expected=dict(source_run=38305592967,qualified=True,added_buffers=76,resized_cells=8,
        minimum_fast_hold_ns=.05,all_original_connections_audited=True,source_detailed_wires_cleared=True,
        full_reroute=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    if gates!=expected:raise ValueError('Wrong combined strict qualification')


def validate_checkpoint(root,proposal,baseline,layout):
    if json.loads((root/'proposal.json').read_text())!=json.loads(json.dumps(proposal)):
        raise ValueError('Wrong canonical combined proposal')
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
    validate_change(before,edited,proposal);validate_antenna_only_changes(edited,Path(state['nl']).read_text())
    validate_placements(layout,Path(state['def']).read_text(),proposal)
    log=(raw.parent/'openroad-globalrouting.log').read_text();validate_overflow(log);require_live_demand(log)
    return source


def main():
    root=Path('runs/combined-physical-screen')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),json.loads((root/'gates.json').read_text()))
    original=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),json.loads(Path('/tmp/native-trusted-files.json').read_text()),fingerprints(Path.cwd()),profile='clock8')
    macro=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macro)!=1 or len(std)!=1:raise ValueError('Missing pinned combined geometry')
    ref=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((ref/'tt_um_tripwire.nl.v').read_text(),(ref/'tt_um_tripwire.def').read_text(),std[0],macro[0],clean_postgpl=True)
    config=configure(json.loads(Path('/tmp/native-trusted-config.json').read_text()),bank,electrical=True)
    if config!=json.loads(Path('src/config_combined_physical_screen.json').read_text()):raise ValueError('Wrong complete combined recipe')
    old=Path('runs/electrical-incremental-route/drt/1-openroad-detailedrouting')
    baseline=(old/'tt_um_tripwire.nl.v').read_text();layout=(old/'tt_um_tripwire.def').read_text()
    sta=unique(Path('runs/extracted-timing'),'*openroad-stapostpnr/state_out.json').parent
    proposal=plan(baseline,layout,(sta/'nom_fast_1p32V_m40C/min.rpt').read_text(),
        {c:(sta/c/'checks.rpt').read_text() for c in ('nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C')},std[0],macro[0])
    source=validate_checkpoint(root,proposal,baseline,layout)
    # Keep original extracted evidence, make fresh output available to the
    # existing zero-DRC extraction helper. No repair or full GRT repeated.
    output=Path('runs/combined-physical-route')
    if Path('runs/extracted-timing').exists():Path('runs/extracted-timing').rename(Path('runs/combined-source-extracted-timing'))
    continue_route(config,source,output,source_run=SOURCE_RUN)


if __name__=='__main__':main()
