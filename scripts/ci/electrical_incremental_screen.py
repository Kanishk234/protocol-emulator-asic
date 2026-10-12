"""Bounded ten-buffer repair with audited incremental routing; no DRT."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from electrical_repair_plan import plan, target_call, validate_change
from event_nor2_screen import logical_cells, validate_antenna_only_changes, validate_overflow
from incremental_repair_audit import audit, added_antenna_nets, require_live_demand, reported_antenna_nets
from native_stock_route import fingerprints, qualified, run_step, validate_source
from postgrt_timing import screen
from route_restore_screen import SEGMENT_SHA
from route_segment_audit import compare
from sram_bank_clean_route import unique
from sram_bank_clean_screen import configure, electrical_clean
from sram_bank_plan import plan as bank_plan, MACRO_LEF_SHA

SOURCE_RUN=38294805019
SOURCE_SHA='ef6259831d3a5531931ff82ae65bda16698d54ae'


def validate_provenance(run,gates):
    if (run.get('id')!=SOURCE_RUN or run.get('head_sha')!=SOURCE_SHA
            or run.get('head_branch')!='main' or run.get('conclusion')!='success'
            or run.get('path')!='.github/workflows/gds-route-restore-screen.yaml'):
        raise ValueError('Wrong verified incremental restoration source')
    expected=dict(exact_segment_roundtrip=True,unchanged_routes_preserved=True,
        unchanged_netlist=True,physical_change_applied=False,official_signoff=False,
        source_run=38293466146,matched_timing=True,no_edit_incremental=True,
        diagnostic_only=True,source_physical_qualified=False)
    if gates!=expected:raise ValueError('Wrong route restoration receipt')


def promote(path):
    state=json.loads(path.read_text());odb=Path(state['odb'])
    for field,suffix in [('nl','.incremental.nl.v'),('pnl','.incremental.pnl.v')]:
        p=odb.with_suffix(suffix)
        if not p.is_file():raise ValueError('Missing fresh incremental '+field)
        state[field]=str(p.resolve())
    state.update(spef=None,sdf=None,lib=None)
    promoted=path.with_name('eco_state.json');promoted.write_text(json.dumps(state,indent=2)+'\n')
    return promoted


def main():
    root=Path('runs/route-restore-screen')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                        json.loads((root/'gates.json').read_text()))
    trusted=json.loads(Path('/tmp/native-trusted-config.json').read_text())
    original_run=dict(id=37990280838,head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
        head_branch='main',conclusion='success',path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original_run,json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),json.loads(Path('/tmp/native-trusted-files.json').read_text()),
        fingerprints(Path.cwd()),profile='clock8')
    macros=[p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest()==MACRO_LEF_SHA]
    std=[p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef')
        if hashlib.sha256(p.read_bytes()).hexdigest()=='c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macros)!=1 or len(std)!=1:raise ValueError('Missing pinned geometry')
    ref=Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    bank=bank_plan((ref/'tt_um_tripwire.nl.v').read_text(),(ref/'tt_um_tripwire.def').read_text(),std[0],macros[0],clean_postgpl=True)
    config=configure(trusted,bank,electrical=True)
    if config!=json.loads(Path('src/config_route_restore_screen.json').read_text()):raise ValueError('Wrong full restoration recipe')
    comparison=json.loads((root/'timing/comparison.json').read_text())
    source=Path(comparison['after_state'])
    if source.resolve()!=unique(root/'restore','*-openroad-globalrouting/state_out.json').resolve():
        raise ValueError('Wrong restored physical state')
    state=json.loads(source.read_text());layout=Path(state['def']);baseline=source.parent/'restored.nl.v'
    if logical_cells(baseline.read_text())!=logical_cells(Path(state['nl']).read_text()):raise ValueError('Restored ODB/netlist mismatch')
    segments=Path(json.loads(Path('runs/electrical-finish-screen/gates.json').read_text())['route_segments'])
    if hashlib.sha256(segments.read_bytes()).hexdigest()!=SEGMENT_SHA:raise ValueError('Wrong exact route segment baseline')
    original=segments.read_text()
    if not compare(original,(source.parent/'noop.segments').read_text())['exact_roundtrip']:
        raise ValueError('Restored routes differ from capture')
    checks=root/'timing/after-nom_slow_1p08V_125C/1-openroad-stamidpnr/checks.rpt'
    proposal=plan(layout.read_text(),checks.read_text(),std[0],macros[0],incremental=True)
    target=Path('workflow-src/scripts/ci/electrical_incremental_targets.tcl')
    if target.exists():raise ValueError('Repeated incremental repair')
    target.write_text(target_call(layout.read_text(),proposal))
    if not re.fullmatch(r'[A-Za-z0-9_./-]+',str(segments.resolve())):raise ValueError('Unsafe segment input path')
    output=Path('runs/electrical-incremental-screen');output.mkdir(exist_ok=False)
    (output/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
    subprocess.run(['docker','build','-t','tripwire-electrical-incremental:local','-f',
        'workflow-src/scripts/ci/Dockerfile.openroad-electrical-incremental','workflow-src/scripts/ci'],check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE']='tripwire-electrical-incremental:local'
    run_step(config,source,output/'incremental',['OpenROAD.GlobalRouting'])
    raw=unique(output/'incremental','*-openroad-globalrouting/state_out.json');changed=promote(raw)
    changed_state=json.loads(changed.read_text())
    before=(raw.parent/'baseline.nl.v').read_text()
    if logical_cells(before)!=logical_cells(baseline.read_text()):raise ValueError('Incremental input ODB changed')
    rebased_segments=(raw.parent/'baseline.segments').read_text()
    after_buffers=(raw.parent/'after_buffers.nl.v').read_text()
    validate_change(before,after_buffers,proposal)
    validate_overflow((raw.parent/'openroad-globalrouting.log').read_text())
    require_live_demand((raw.parent/'openroad-globalrouting.log').read_text())
    audit(layout.read_text(),(raw.parent/'after_buffers.def').read_text(),rebased_segments,
          (raw.parent/'after_buffers.segments').read_text(),proposal)
    final=changed_state
    antenna_nets=added_antenna_nets(after_buffers,Path(final['nl']).read_text())
    # Jumper repairs change geometry without adding diode instances. Permit
    # only nets independently reported as violating before repair.
    reported_nets=reported_antenna_nets((raw.parent/'before_antenna.rpt').read_text())
    repair_nets=sorted(set(antenna_nets)|set(reported_nets))
    preservation=audit(layout.read_text(),Path(final['def']).read_text(),rebased_segments,
        Path(final['odb']).with_suffix('.segments').read_text(),proposal,antenna_nets=repair_nets)
    run_step(config,changed,output/'antenna',['OpenROAD.CheckAntennas'])
    checked=unique(output/'antenna','*-openroad-checkantennas/state_out.json')
    antenna=json.loads((checked.parent/'or_metrics_out.json').read_text())
    # Baseline is explicitly the one live full route, not the older segment snapshot.
    rebased=dict(state)
    rebased['odb']=str((raw.parent/'rebased.odb').resolve())
    rebased['def']=str((raw.parent/'rebased.def').resolve())
    rebased['nl']=str((raw.parent/'rebased.nl.v').resolve())
    rebased.update(spef=None,sdf=None,lib=None)
    before_state=raw.parent/'rebased_state.json';before_state.write_text(json.dumps(rebased,indent=2)+'\n')
    path=Path('src/config_electrical_incremental_screen.json');path.write_text(json.dumps(config,indent=2)+'\n')
    screen(path,before_state,output/'timing',os.environ['PDK_ROOT'],repaired=checked,sdc=Path('src/signoff.sdc'))
    timing=json.loads((output/'timing/comparison.json').read_text())
    timing_ready=qualified(timing,antenna);electrical_ready=electrical_clean(timing)
    gates=dict(source_run=SOURCE_RUN,qualified=timing_ready and electrical_ready,
        timing_antenna_qualified=timing_ready,electrical_qualified=electrical_ready,
        added_buffers=proposal['added_buffers'],minimum_fast_hold_ns=.05,
        unrelated_routes_preserved_after_rebase=preservation['unchanged_routes_preserved'],
        initial_full_route=True,live_capacity_initialized=True,
        rebase_changed_route_nets=compare(original,rebased_segments)['changed_nets'],
        antenna_repaired_nets=antenna_nets,pre_repair_antenna_violation_nets=reported_nets,
        changed_route_nets=preservation['changed_nets'],custom_image=True,physical_screen_only=True,official_signoff=False)
    (output/'gates.json').write_text(json.dumps(gates,indent=2)+'\n')
    if not gates['qualified']:raise ValueError('Incremental electrical screen fails strict physical gates')


if __name__=='__main__':main()
