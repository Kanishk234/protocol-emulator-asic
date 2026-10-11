"""Clean stock Classic screen with one built-in SRAM placement policy."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from event_nor2_screen import logical_cells, validate_overflow
from native_stock_route import fingerprints, qualified, run_step
from native_stock_screen import checkpoint
from residual_data_screen import validate_inputs
from postgrt_timing import screen
from sram_bank_plan import plan, placement_fragment, MACRO_LEF_SHA


def configure(original, proposal):
    if (original.get('CLOCK_PERIOD') != 20 or original.get('PL_TARGET_DENSITY_PCT') != 56
            or original.get('SYNTH_STRATEGY') != 'AREA 1'
            or original.get('GRT_RESIZER_HOLD_SLACK_MARGIN') != .10
            or original.get('CTS_SINK_CLUSTERING_SIZE') != 8
            or original.get('meta', {}).get('flow') != 'Classic'
            or original.get('meta', {}).get('substituting_steps')
            or original.get('MANUAL_GLOBAL_PLACEMENTS')):
        raise ValueError('Wrong clean stock baseline recipe')
    if proposal.get('source_stage') != 'postgpl-clean':
        raise ValueError('Clean placement requires pre-manual-stage geometry')
    return dict(original, GRT_ALLOW_CONGESTION=False, **placement_fragment(proposal))


def verify_stage(layout, proposal):
    import re
    for item in proposal['proposals']:
        x, y, orientation = item['new_location']
        if not re.search(re.escape(item['instance'])+r' sg13cmos5l_buf_4[^;]*PLACED \( '
                         +str(x)+' '+str(y)+r' \) '+orientation+r'\b', layout):
            raise ValueError('Clean SRAM placement missing or changed at '+item['instance'])


def main():
    root = Path.cwd()
    trusted = json.loads(Path('/tmp/native-trusted-config.json').read_text())
    validate_inputs(root, json.loads(Path('/tmp/native-eco-source-run.json').read_text()),
                    json.loads(Path('/tmp/native-trusted-files.json').read_text()), trusted)
    reference = Path('runs/native-stock-screen/flow/32-openroad-repairdesignpostgpl')
    nl, layout = reference/'tt_um_tripwire.nl.v', reference/'tt_um_tripwire.def'
    macros = [p for p in Path('macro').rglob('*.lef')
              if hashlib.sha256(p.read_bytes()).hexdigest() == MACRO_LEF_SHA]
    std = [p for p in (Path(os.environ['PDK_ROOT'])/'ihp-sg13cmos5l/libs.ref').rglob('*.lef')
           if hashlib.sha256(p.read_bytes()).hexdigest()
           == 'c47c436758ae87288324aa1f5a84fcc8faf813bf19df1a400b32258fff4e1219']
    if len(macros) != 1 or len(std) != 1:
        raise ValueError('Missing or ambiguous pinned LEF geometry')
    proposal = plan(nl.read_text(), layout.read_text(), std[0], macros[0], clean_postgpl=True)
    config = configure(trusted, proposal)
    output = Path('runs/sram-bank-clean-screen'); output.mkdir(exist_ok=False)
    (output/'proposal.json').write_text(json.dumps(proposal, indent=2)+'\n')
    path = Path('src/config_sram_bank_clean.json'); path.write_text(json.dumps(config, indent=2)+'\n')
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    flow = output/'flow'
    subprocess.run([sys.executable, '-m', 'librelane', '--pdk-root', os.environ['PDK_ROOT'],
        '--docker-no-tty', '--dockerized', '--pdk', 'ihp-sg13cmos5l', '--manual-pdk',
        '--run-tag', 'sram-bank-clean', '--force-run-dir', str(flow), '--hide-progress-bar',
        '--to', 'OpenROAD.ResizerTimingPostGRT', str(path)], check=True)
    before = list(flow.glob('*-openroad-repairdesignpostgpl/tt_um_tripwire.nl.v'))
    placed = list(flow.glob('*-odb-manualglobalplacement/tt_um_tripwire.def'))
    legalized = list(flow.glob('*-openroad-detailedplacement/tt_um_tripwire.def'))
    if len(before) != 1 or len(placed) != 1 or len(legalized) != 1:
        raise ValueError('Missing clean placement history')
    if logical_cells(before[0].read_text()) != logical_cells(nl.read_text()):
        raise ValueError('Clean pre-placement topology does not reproduce reference')
    for stage in (placed[0], legalized[0]): verify_stage(stage.read_text(), proposal)
    routing_logs = list(flow.glob('*-openroad-globalrouting/openroad-globalrouting.log'))
    if len(routing_logs) != 1: raise ValueError('Missing clean routing evidence')
    validate_overflow(routing_logs[0].read_text())
    source = checkpoint(flow)
    antenna = output/'antenna'
    run_step(config, source, antenna, ['OpenROAD.CheckAntennas'])
    metrics = list(antenna.glob('*-openroad-checkantennas/or_metrics_out.json'))
    if len(metrics) != 1: raise ValueError('Missing fresh antenna evidence')
    screen(path, source, output/'timing', os.environ['PDK_ROOT'], repaired=source, sdc=Path('src/signoff.sdc'))
    ready = qualified(json.loads((output/'timing/comparison.json').read_text()), json.loads(metrics[0].read_text()))
    (output/'gates.json').write_text(json.dumps(dict(source_run=38172640071,
        clean_from_rtl=True, stock_classic=True, custom_image=False,
        added_cells_by_policy=0, relocated_instances=len(proposal['proposals']),
        qualified=ready, minimum_fast_hold_ns=.05, physical_screen_only=True,
        official_signoff=False), indent=2)+'\n')
    if not ready: raise ValueError('Clean bank screen fails timing/50ps hold/antenna gate')


if __name__ == '__main__': main()
