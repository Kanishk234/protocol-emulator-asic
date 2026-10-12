"""Repair exact electrical screen checkpoint; strict screen gates, no DRT."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
from event_nor2_screen import validate_antenna_only_changes, validate_overflow
from native_stock_route import fingerprints, run_step, validate_source, qualified
from postgrt_timing import screen
from sram_bank_clean_route import unique, validate_checkpoint
from sram_bank_clean_screen import configure, electrical_clean
from sram_bank_plan import plan as bank_plan, MACRO_LEF_SHA
from electrical_repair_plan import plan, target_call, validate_change, DEF_SHA
from clock8_residual_screen import promote_antenna

SOURCE_RUN=38272508875
SOURCE_SHA='9a65064a2cf51d10577e416acabd74d1fad46758'


def validate_provenance(run, gates):
    if (run.get('id')!=SOURCE_RUN or run.get('head_sha')!=SOURCE_SHA
            or run.get('head_branch')!='main' or run.get('conclusion')!='success'
            or run.get('path')!='.github/workflows/gds-sram-bank-electrical-screen.yaml'):
        raise ValueError('Wrong measured electrical source')
    expected=dict(source_run=38172640071,clean_from_rtl=True,stock_classic=True,
        custom_image=False,added_cells_by_policy=0,relocated_instances=16,qualified=True,
        minimum_fast_hold_ns=.05,physical_screen_only=True,official_signoff=False,
        native_postgrt_electrical_repair=True,setup_repair_target_ns=0.0,
        hold_repair_target_ns=.125,slew_margin_pct=10,cap_margin_pct=10)
    if gates!=expected: raise ValueError('Wrong legacy timing-qualified screen receipt')
    # Legacy qualified means timing/antenna only, not electrically qualified.


def main():
    root=Path('runs/sram-bank-electrical-screen')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                        json.loads((root/'gates.json').read_text()))
    trusted=json.loads(Path('/tmp/native-trusted-config.json').read_text())
    original_run=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
        head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original_run,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),
        json.loads(Path('/tmp/native-trusted-files.json').read_text()),fingerprints(Path.cwd()),profile='clock8')
    macros=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef')
         if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macros)!=1 or len(std)!=1: raise ValueError('Missing pinned geometry')
    reference=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((reference/'tt_um_tripwire.nl.v').read_text(),(reference/'tt_um_tripwire.def').read_text(),std[0],macros[0],clean_postgpl=True)
    if bank!=json.loads((root/'proposal.json').read_text()): raise ValueError('Changed bank policy')
    config=configure(trusted,bank,electrical=True)
    if config!=json.loads(Path('src/config_sram_bank_electrical.json').read_text()): raise ValueError('Changed source recipe')
    source=validate_checkpoint(root,bank)
    saved=json.loads(source.read_text()); layout=Path(saved['def'])
    if hashlib.sha256(layout.read_bytes()).hexdigest()!=DEF_SHA: raise ValueError('Wrong final DEF')
    if list(root.rglob('*-openroad-detailedrouting')): raise ValueError('Source contains DRT')
    checks=root/'timing/after-nom_slow_1p08V_125C/1-openroad-stamidpnr/checks.rpt'
    proposal=plan(layout.read_text(),checks.read_text(),std[0],macros[0])
    targets=Path('workflow-src/scripts/ci/electrical_repair_targets.tcl')
    if targets.exists(): raise ValueError('Repeated electrical repair')
    targets.write_text(target_call(layout.read_text(),proposal))
    output=Path('runs/electrical-repair-screen');output.mkdir(exist_ok=False)
    (output/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    subprocess.run(['docker','build','-t','tripwire-electrical-repair:local','-f',
        'workflow-src/scripts/ci/Dockerfile.openroad-electrical-repair','workflow-src/scripts/ci'],check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE']='tripwire-electrical-repair:local'
    run_step(config,source,output/'grt',['OpenROAD.GlobalRouting'])
    changed=unique(output/'grt','*-openroad-globalrouting/state_out.json')
    state=json.loads(changed.read_text());odb=Path(state['odb'])
    before=odb.with_suffix('.baseline.nl.v');nl=odb.with_suffix('.eco.nl.v');pnl=odb.with_suffix('.eco.pnl.v')
    validate_antenna_only_changes(Path(saved['nl']).read_text(),before.read_text())
    validate_change(before.read_text(),nl.read_text(),proposal)
    log=(changed.parent/'openroad-globalrouting.log').read_text()
    if log.count('TRIPWIRE electrical repair:')!=27: raise ValueError('Wrong repair count')
    validate_overflow(log)
    state.update(nl=str(nl.resolve()),pnl=str(pnl.resolve()),spef=None,sdf=None,lib=None)
    promoted=changed.with_name('eco_state.json');promoted.write_text(json.dumps(state,indent=2)+'\n')
    run_step(config,promoted,output/'antenna',['OpenROAD.CheckAntennas'])
    checked=unique(output/'antenna','*-openroad-checkantennas/state_out.json')
    metrics=json.loads((checked.parent/'or_metrics_out.json').read_text())
    if metrics.get('antenna__violating__nets') or metrics.get('antenna__violating__pins'):
        run_step(config,checked,output/'antenna-cleanup',['OpenROAD.RepairAntennas','OpenROAD.CheckAntennas'])
        checked=unique(output/'antenna-cleanup','*-openroad-checkantennas/state_out.json')
        metrics=json.loads((checked.parent/'or_metrics_out.json').read_text())
        resolved=json.loads((output/'antenna-cleanup/resolved.json').read_text())
        log=unique(output/'antenna-cleanup','*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
        if resolved.get('GRT_ALLOW_CONGESTION') is not False or '-allow_congestion' in log or 'repair_antennas' not in log:
            raise ValueError('Wrong cleanup congestion policy')
        checked=promote_antenna(checked,nl)
    path=Path('src/config_electrical_repair_screen.json');path.write_text(json.dumps(config,indent=2)+'\n')
    screen(path,checked,output/'timing',os.environ['PDK_ROOT'],repaired=checked,sdc=Path('src/signoff.sdc'))
    comparison=json.loads((output/'timing/comparison.json').read_text())
    timing_ready=qualified(comparison,metrics);electrical_ready=electrical_clean(comparison)
    ready=timing_ready and electrical_ready
    (output/'gates.json').write_text(json.dumps(dict(source_run=SOURCE_RUN,qualified=ready,
        timing_antenna_qualified=timing_ready,electrical_qualified=electrical_ready,
        added_buffers=27,minimum_fast_hold_ns=.05,physical_screen_only=True,
        custom_image=True,official_signoff=False),indent=2)+'\n')
    if not ready: raise ValueError('Electrical repair screen fails strict timing/electrical/antenna gates')


if __name__=='__main__': main()
