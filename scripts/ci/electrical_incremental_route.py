"""Route the qualified live electrical checkpoint without repeating repairs."""
import hashlib
import json
import os
from pathlib import Path
from event_nor2_screen import validate_overflow
from native_stock_route import fingerprints, qualified, run_step, validate_source
from postgrt_timing import screen
from sram_bank_clean_screen import configure, electrical_clean
from sram_bank_clean_route import unique, validate_final_route
from sram_bank_plan import plan as bank_plan, MACRO_LEF_SHA

SOURCE_RUN=38304235648
SOURCE_SHA='f069c10f3fe6cb7f29a987d2e8c0c7669ce72fec'


def validate_provenance(run,gates):
    expected=dict(id=SOURCE_RUN,head_sha=SOURCE_SHA,head_branch='main',conclusion='success',
                  path='.github/workflows/gds-electrical-incremental-screen.yaml')
    if any(run.get(k)!=v for k,v in expected.items()):
        raise ValueError('Wrong qualified live electrical source')
    expected=dict(source_run=38294805019,qualified=True,timing_antenna_qualified=True,
        electrical_qualified=True,added_buffers=10,minimum_fast_hold_ns=.05,
        unrelated_routes_preserved_after_rebase=True,initial_full_route=True,
        live_capacity_initialized=True,custom_image=True,physical_screen_only=True,official_signoff=False)
    if any(gates.get(k)!=v for k,v in expected.items()):
        raise ValueError('Unqualified live electrical screen')


def validate_checkpoint(root):
    comparison=json.loads((root/'timing/comparison.json').read_text())
    source=unique(root/'antenna','*-openroad-checkantennas/state_out.json')
    if Path(comparison['after_state']).resolve()!=source.resolve():
        raise ValueError('Wrong measured live checkpoint')
    antenna=json.loads((source.parent/'or_metrics_out.json').read_text())
    if not qualified(comparison,antenna) or not electrical_clean(comparison):
        raise ValueError('Saved live electrical gates fail')
    raw=unique(root/'incremental','*-openroad-globalrouting/state_out.json')
    from incremental_repair_audit import require_live_demand
    log=(raw.parent/'openroad-globalrouting.log').read_text()
    validate_overflow(log);require_live_demand(log)
    state=json.loads(source.read_text())
    raw_state=json.loads(raw.read_text())
    for key in ('odb','def','nl','pnl','sdc'):
        if not Path(state[key]).is_file():raise ValueError('Missing live checkpoint '+key)
        expected=Path(raw_state[key])
        if key in ('nl','pnl'):expected=Path(raw_state['odb']).with_suffix('.incremental.'+key+'.v')
        if Path(state[key]).resolve()!=expected.resolve():raise ValueError('Stale live checkpoint '+key)
    return source


def continue_route(config,source,output):
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE',None)
    run_step(config,source,output/'antenna',['OpenROAD.CheckAntennas'])
    antenna=json.loads(unique(output/'antenna','*-openroad-checkantennas/or_metrics_out.json').read_text())
    path=Path('src/config_electrical_incremental_route.json');path.write_text(json.dumps(config,indent=2)+'\n')
    screen(path,source,output/'timing',os.environ['PDK_ROOT'],repaired=source,sdc=Path('src/signoff.sdc'))
    timing=json.loads((output/'timing/comparison.json').read_text())
    ready=qualified(timing,antenna) and electrical_clean(timing)
    (output/'gates.json').write_text(json.dumps(dict(source_run=SOURCE_RUN,qualified=ready,
        minimum_fast_hold_ns=.05,repair_repeated=False,official_signoff=False),indent=2)+'\n')
    if not ready:raise ValueError('Fresh electrical/timing/antenna gates fail; DRT refused')
    run_step(config,source,output/'drt',['OpenROAD.DetailedRouting'])
    validate_final_route(source,output/'drt')
    Path('src/config_merged.json').write_text(json.dumps(config,indent=2)+'\n')
    if Path('runs/extracted-timing').exists():raise ValueError('Unexpected old extraction output')
    from extracted_timing import main as extract
    extract(output/'drt')
    extracted=Path('runs/extracted-timing')
    summary=json.loads((extracted/'corner_summary.json').read_text())
    electrical=json.loads((extracted/'electrical_summary.json').read_text())
    corners={c:{'after':summary} for c in timing['corners']}
    final_ant=json.loads(unique(extracted,'*-openroad-checkantennas/or_metrics_out.json').read_text())
    extracted_ready=qualified({'corners':corners},final_ant) and all(
        row['no_reported_electrical_violations'] for row in electrical.values())
    (output/'extracted_gates.json').write_text(json.dumps(dict(qualified=extracted_ready,
        source_run=SOURCE_RUN,minimum_fast_hold_ns=.05,official_signoff=False),indent=2)+'\n')
    if not extracted_ready:raise ValueError('Extracted timing/electrical/antenna gates fail')


def main():
    root=Path('runs/electrical-incremental-screen')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                        json.loads((root/'gates.json').read_text()))
    original_run=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
        head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original_run,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),
        json.loads(Path('/tmp/native-trusted-files.json').read_text()),fingerprints(Path.cwd()),profile='clock8')
    macros=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef')
         if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macros)!=1 or len(std)!=1:raise ValueError('Missing pinned bank geometry')
    ref=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((ref/'tt_um_tripwire.nl.v').read_text(),(ref/'tt_um_tripwire.def').read_text(),std[0],macros[0],clean_postgpl=True)
    config=configure(json.loads(Path('/tmp/native-trusted-config.json').read_text()),bank,electrical=True)
    if config!=json.loads(Path('src/config_electrical_incremental_screen.json').read_text()):
        raise ValueError('Wrong full live physical recipe')
    source=validate_checkpoint(root)
    continue_route(config,source,Path('runs/electrical-incremental-route'))


if __name__=='__main__':main()
