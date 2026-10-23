"""Stock GDS/Magic DRC/LVS tail diagnostic on the exact passing route.

No placement/routing edits, checkpoint repair, or official-flow claim.
KLayout DRC/XOR are disabled in the bound IHP recipe; this does not certify them.
"""
import hashlib
import json
import os
from pathlib import Path

from native_stock_route import run_step
from sram_bank_clean_route import unique
from wire600_mux_routed_gl import validate as validate_route

PROFILE = json.loads((Path(__file__).parent/'fixtures/wire600_selective/mux_signoff.json').read_text())
STEPS = [
    'Magic.StreamOut', 'KLayout.StreamOut', 'Magic.WriteLEF',
    'Odb.CheckDesignAntennaProperties', 'Magic.DRC', 'Checker.MagicDRC',
    'Magic.SpiceExtraction', 'Checker.IllegalOverlap', 'Netgen.LVS',
    'Checker.LVS', 'Misc.ReportManufacturability',
]
FRESH_METRICS = {
    '*-magic-drc/state_out.json': 'magic__drc_error__count',
    '*-magic-spiceextraction/state_out.json': 'magic__illegal_overlap__count',
    '*-netgen-lvs/state_out.json': 'design__lvs_error__count',
}


def validate_source(root, run):
    root = Path(root)
    result = validate_route(root, run)
    for name, expected in PROFILE['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Changed signoff source view: '+name)
    config = json.loads((root/'src/config_electrical_incremental_route.json').read_text())
    for key in ('ERROR_ON_MAGIC_DRC', 'ERROR_ON_ILLEGAL_OVERLAPS'):
        if config.get(key) is not True:
            raise ValueError('Strict signoff error gate required: '+key)
    state = json.loads((root/PROFILE['source_state']).read_text())
    if any(key in state['metrics'] for key in FRESH_METRICS.values()):
        raise ValueError('Source unexpectedly contains inherited signoff metrics')
    return result, config


def collect(output):
    output = Path(output)
    measured = {}
    for pattern, key in FRESH_METRICS.items():
        state = json.loads(unique(output, pattern).read_text())
        value = state['metrics'].get(key)
        if type(value) not in (int, float) or value != 0:
            raise ValueError('Fresh signoff metric missing or failing: '+key)
        measured[key] = value
    for stage, view in (('magic-streamout', 'mag_gds'),
                        ('klayout-streamout', 'klayout_gds')):
        state = json.loads(unique(output, '*-'+stage+'/state_out.json').read_text())
        gds = Path(state.get(view, ''))
        if (not gds.is_file() or gds.stat().st_size == 0
                or gds.parent.resolve() != unique(output, '*-'+stage+'/state_out.json').parent.resolve()):
            raise ValueError('Missing fresh '+stage+' GDS')
    return dict(source_run=PROFILE['source_run'], fresh_metrics=measured,
                diagnostic_tail_pass=True, official_signoff=False,
                klayout_drc_verified=False, xor_verified=False)


def main():
    root = Path.cwd()
    run = json.loads(Path('/tmp/signoff-source-run.json').read_text())
    _, config = validate_source(root, run)
    source = root/PROFILE['source_state']
    # State paths must resolve in the original runner workspace. Never silently
    # rebase a checkpoint or let LibreLane read another run's similarly named views.
    state = json.loads(source.read_text())
    for key in ('odb', 'def', 'nl', 'pnl'):
        path = Path(state[key])
        if not path.is_file() or str(path.relative_to(root)) not in PROFILE['files']:
            raise ValueError('Signoff state path outside bound workspace: '+key)
    os.environ.pop('LIBRELANE_IMAGE_OVERRIDE', None)
    output = Path('runs/wire600-mux-signoff')
    # The route artifact omits synthesis JSON/header views. None of these tail
    # steps consumes them; retain every physical/netlist/constraint view intact.
    for key in PROFILE['omitted_unused_views']:
        state.pop(key, None)
    initial = Path('runs/wire600-mux-signoff-input.json')
    if initial.exists() or output.exists():
        raise ValueError('Signoff diagnostic requires a fresh output directory')
    initial.write_text(json.dumps(state, indent=2)+'\n')
    run_step(config, initial, output, STEPS)
    receipt = collect(output)
    # Revalidate all immutable inputs after physical verification.
    validate_source(root, run)
    (output/'gates.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
