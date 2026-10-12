"""Audit successful clean SRAM placement, then stock DRT and fresh extraction."""
import json
import os
from pathlib import Path
from event_nor2_screen import logical_cells, validate_antenna_only_changes, validate_overflow
from native_stock_route import fingerprints, qualified, run_step, validate_source
from postgrt_timing import screen
from sram_bank_plan import plan, MACRO_LEF_SHA
from sram_bank_clean_screen import configure, verify_stage
import hashlib

SOURCE_RUN = 38184574265
SOURCE_SHA = '96b19be921b9cafc83b3e8b51cd5eb5f139cabba'


def validate_provenance(run, gates):
    if (run.get('id') != SOURCE_RUN or run.get('head_sha') != SOURCE_SHA
            or run.get('head_branch') != 'main' or run.get('conclusion') != 'success'
            or run.get('path') != '.github/workflows/gds-sram-bank-clean-screen.yaml'):
        raise ValueError('Wrong qualified clean-bank source')
    expected = dict(source_run=38172640071, clean_from_rtl=True, stock_classic=True,
                    custom_image=False, added_cells_by_policy=0, relocated_instances=16,
                    qualified=True, minimum_fast_hold_ns=.05, physical_screen_only=True,
                    official_signoff=False)
    if gates != expected:
        raise ValueError('Wrong clean-bank qualification gate')


def unique(root, pattern):
    files = list(root.glob(pattern))
    if len(files) != 1: raise ValueError('Missing unique clean-bank view: '+pattern)
    return files[0]


def validate_final_route(source, drt):
    # Stock antenna cleanup updates ODB/DEF but can inherit the prior NL view.
    # DRT exports a fresh NL from that actual database; audit it before extraction.
    before = json.loads(source.read_text())
    after = json.loads(unique(drt, '*-openroad-detailedrouting/state_out.json').read_text())
    validate_antenna_only_changes(Path(before['nl']).read_text(), Path(after['nl']).read_text())


def validate_checkpoint(root, proposal):
    timing = json.loads((root/'timing/comparison.json').read_text())
    source = Path(timing['after_state'])
    flow = root/'flow'
    initial = unique(flow, '*-openroad-resizertimingpostgrt/state_out.json')
    allowed = [initial]
    cleanup = root/'antenna-cleanup'
    if cleanup.exists():
        checked = unique(cleanup, '*-openroad-checkantennas/state_out.json')
        allowed.append(checked)
        resolved = json.loads((cleanup/'resolved.json').read_text())
        log = unique(cleanup, '*-openroad-repairantennas/*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
        if resolved.get('GRT_ALLOW_CONGESTION') is not False or 'repair_antennas' not in log or '-allow_congestion' in log:
            raise ValueError('Wrong clean-bank antenna routing policy')
    if source.resolve() not in [p.resolve() for p in allowed]:
        raise ValueError('Wrong clean-bank timing checkpoint')
    is_initial = source.resolve() == initial.resolve()
    metrics_root = unique(root/'antenna', '*-openroad-checkantennas/or_metrics_out.json').parent if is_initial else source.parent
    antenna = json.loads((metrics_root/'or_metrics_out.json').read_text())
    if not qualified(timing, antenna): raise ValueError('Saved clean-bank timing/antenna gate fails')
    reference = Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v')
    before = unique(flow, '*-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v')
    if logical_cells(before.read_text()) != logical_cells(reference.read_text()):
        raise ValueError('Clean-bank pre-placement topology mismatch')
    verify_stage(unique(flow, '*-odb-manualglobalplacement/tt_um_tripwire.def').read_text(), proposal)
    verify_stage(unique(flow, '*-openroad-detailedplacement/tt_um_tripwire.def').read_text(), proposal)
    validate_overflow(unique(flow, '*-openroad-globalrouting/openroad-globalrouting.log').read_text())
    state = json.loads(source.read_text())
    if not is_initial:
        original = json.loads(initial.read_text())
        validate_antenna_only_changes(Path(original['nl']).read_text(), Path(state['nl']).read_text())
    for key in ('odb', 'def', 'nl', 'pnl', 'sdc'):
        if not Path(state[key]).is_file(): raise ValueError('Missing clean-bank checkpoint '+key)
    return source


def main():
    root = Path('runs/sram-bank-clean-screen')
    validate_provenance(json.loads(Path('/tmp/native-strength-source-run.json').read_text()),
                        json.loads((root/'gates.json').read_text()))
    trusted = json.loads(Path('/tmp/native-trusted-config.json').read_text())
    original_run = dict(id=37990280838, head_sha='dfe1a9f46d9b97d20550d1326fb7755cbe2829cf',
        head_branch='main', conclusion='success', path='.github/workflows/gds-native-clock8-screen.yaml')
    validate_source(original_run, json.loads(Path('runs/native-stock-screen/recipe.json').read_text()),
        json.loads(Path('src/config_native_stock.json').read_text()),
        json.loads(Path('/tmp/native-trusted-files.json').read_text()), fingerprints(Path.cwd()), profile='clock8')
    macros = [p for p in Path('macro').rglob('*.lef') if hashlib.sha256(p.read_bytes()).hexdigest() == MACRO_LEF_SHA]
    std = [p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef')
        if hashlib.sha256(p.read_bytes()).hexdigest() == 'c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macros) != 1 or len(std) != 1: raise ValueError('Missing unique pinned bank geometry')
    reference = Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    proposal = plan((reference/'tt_um_tripwire.nl.v').read_text(), (reference/'tt_um_tripwire.def').read_text(),
                    std[0], macros[0], clean_postgpl=True)
    if proposal != json.loads((root/'proposal.json').read_text()): raise ValueError('Wrong saved clean-bank proposal')
    config = configure(trusted, proposal)
    if config != json.loads(Path('src/config_sram_bank_clean.json').read_text()):
        raise ValueError('Wrong clean-bank full physical recipe')
    if list(root.rglob('*-openroad-detailedrouting')): raise ValueError('Clean screen already contains DRT')
    source = validate_checkpoint(root, proposal)
    continue_route(config, source, Path('runs/sram-bank-clean-route'))


def continue_route(config, source, output):
    output.mkdir(exist_ok=False)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    run_step(config, source, output/'antenna', ['OpenROAD.CheckAntennas'])
    metrics = json.loads(unique(output/'antenna', '*-openroad-checkantennas/or_metrics_out.json').read_text())
    path = Path('src/config_sram_bank_clean_route.json'); path.write_text(json.dumps(config, indent=2)+'\n')
    screen(path, source, output/'timing', os.environ['PDK_ROOT'], repaired=source, sdc=Path('src/signoff.sdc'))
    ready = qualified(json.loads((output/'timing/comparison.json').read_text()), metrics)
    (output/'gates.json').write_text(json.dumps(dict(source_run=SOURCE_RUN, qualified=ready,
        minimum_fast_hold_ns=.05, repair_repeated=False, state=str(source), official_signoff=False), indent=2)+'\n')
    if not ready: raise ValueError('Fresh clean-bank timing/antenna gate fails')
    run_step(config, source, output/'drt', ['OpenROAD.DetailedRouting'])
    validate_final_route(source, output/'drt')
    Path('src/config_merged.json').write_text(json.dumps(config, indent=2)+'\n')
    if Path('runs/extracted-timing').exists(): Path('runs/extracted-timing').rename(output/'source-extracted-timing')
    from extracted_timing import main as extract
    extract(output/'drt')


if __name__ == '__main__': main()
