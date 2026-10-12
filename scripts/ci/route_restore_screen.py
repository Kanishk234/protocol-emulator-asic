"""Exact segment restoration and no-edit incremental diagnostic; no repair/DRT."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from event_nor2_screen import logical_cells, validate_antenna_only_changes, validate_overflow
from electrical_repair_plan import plan, validate_change
from electrical_repair_screen import same_plan
from native_stock_route import fingerprints, run_step, validate_source
from postgrt_timing import screen
from route_restore_audit import audit_geometry_and_logic, audit_timing
from route_segment_audit import parse
from sram_bank_clean_route import unique
from sram_bank_clean_screen import configure
from sram_bank_plan import plan as bank_plan, MACRO_LEF_SHA

SOURCE_RUN=38293466146
SOURCE_SHA='241f7dd11e4198b5be3a9a7a34f3c910baf3d414'
SEGMENT_SHA='860b8c777de3b4d555ad9967ec4a1487dd540b71cb89e3401b8b36b73a794588'


def validate_provenance(run,gates):
    if (run.get('id')!=SOURCE_RUN or run.get('head_sha')!=SOURCE_SHA
            or run.get('head_branch')!='main' or run.get('conclusion')!='success'
            or run.get('path')!='.github/workflows/gds-route-segment-export.yaml'):
        raise ValueError('Wrong live segment export source')
    required=dict(source_run=38283838612,added_buffers=7,resized_cells=1,minimum_fast_hold_ns=.05,
        physical_screen_only=True,custom_image=True,official_signoff=False,
        route_segment_capture_only=True,checkpoint_restoration_tested=False)
    if any(gates.get(k)!=v for k,v in required.items()): raise ValueError('Wrong segment capture receipt')
    if any(type(gates.get(k)) is not bool for k in ('qualified','timing_antenna_qualified','electrical_qualified')):
        raise ValueError('Missing actual qualification fields')


def main():
    root=Path('runs/electrical-finish-screen')
    gates=json.loads((root/'gates.json').read_text())
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),gates)
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
    config=configure(trusted,bank,electrical=True)
    if config!=json.loads(Path('src/config_electrical_repair_screen.json').read_text()):
        raise ValueError('Wrong full capture recipe')
    parent=Path('runs/electrical-residual-screen')
    parent_state=json.loads(Path(json.loads((parent/'timing/comparison.json').read_text())['after_state']).read_text())
    proposal=plan(Path(parent_state['def']).read_text(),(parent/'timing/after-nom_slow_1p08V_125C/1-openroad-stamidpnr/checks.rpt').read_text(),std[0],macros[0],finish=True)
    if not same_plan(proposal,json.loads((root/'proposal.json').read_text())): raise ValueError('Changed captured physical policy')
    grt=unique(root/'grt','*-openroad-globalrouting/state_out.json')
    odb=Path(json.loads(grt.read_text())['odb'])
    validate_change(odb.with_suffix('.baseline.nl.v').read_text(),odb.with_suffix('.eco.nl.v').read_text(),proposal)
    validate_overflow((grt.parent/'openroad-globalrouting.log').read_text())
    source=Path(json.loads((root/'timing/comparison.json').read_text())['after_state'])
    if source.resolve()!=unique(root/'antenna-cleanup','*-openroad-checkantennas/eco_state.json').resolve():
        raise ValueError('Wrong final captured checkpoint')
    state=json.loads(source.read_text())
    segments=Path(state['odb']).with_suffix('.segments')
    if segments.resolve()!=Path(gates['route_segments']).resolve(): raise ValueError('Segments do not belong to final ODB')
    if hashlib.sha256(segments.read_bytes()).hexdigest()!=SEGMENT_SHA: raise ValueError('Changed captured route segments')
    original=segments.read_text();routes=parse(original)
    if len(routes)!=33909 or sum(map(len,routes.values()))!=268616: raise ValueError('Changed captured route inventory')
    validate_antenna_only_changes(odb.with_suffix('.eco.nl.v').read_text(),Path(state['nl']).read_text())
    if list(root.rglob('*-openroad-detailedrouting')): raise ValueError('Capture unexpectedly contains DRT')
    if not re.fullmatch(r'[A-Za-z0-9_./-]+',str(segments.resolve())): raise ValueError('Unsafe segment path')
    target=Path('workflow-src/scripts/ci/route_restore_targets.tcl')
    if target.exists(): raise ValueError('Repeated restoration diagnostic')
    target.write_text('set tripwire_segments {'+str(segments.resolve())+'}\n')
    output=Path('runs/route-restore-screen');output.mkdir(exist_ok=False)
    subprocess.run(['docker','build','-t','tripwire-route-restore:local','-f',
        'workflow-src/scripts/ci/Dockerfile.openroad-route-restore','workflow-src/scripts/ci'],check=True)
    os.environ['LIBRELANE_IMAGE_OVERRIDE']='tripwire-route-restore:local'
    run_step(config,source,output/'restore',['OpenROAD.GlobalRouting'])
    restored=unique(output/'restore','*-openroad-globalrouting/state_out.json')
    baseline=(restored.parent/'baseline.nl.v').read_text()
    final=(restored.parent/'restored.nl.v').read_text()
    if logical_cells(Path(state['nl']).read_text())!=logical_cells(baseline): raise ValueError('Baseline ODB/netlist mismatch')
    result=audit_geometry_and_logic(original,(restored.parent/'restored.segments').read_text(),
        (restored.parent/'noop.segments').read_text(),baseline,final)
    path=Path('src/config_route_restore_screen.json');path.write_text(json.dumps(config,indent=2)+'\n')
    screen(path,source,output/'timing',os.environ['PDK_ROOT'],repaired=restored,sdc=Path('src/signoff.sdc'))
    audit_timing(json.loads((output/'timing/comparison.json').read_text()))
    result.update(source_run=SOURCE_RUN,matched_timing=True,no_edit_incremental=True,
                  diagnostic_only=True,source_physical_qualified=gates['qualified'])
    (output/'gates.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
