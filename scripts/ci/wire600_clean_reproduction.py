"""Fresh RTL synthesis followed by the unchanged, hash-bound passing repairs.

No checkpoint downloads, new target discovery, detailed routing or signoff claim.
A nonidentical rebuild stops before edits; it must be reviewed independently.
"""
import json
from pathlib import Path

from native_delta8_wire600_screen import main as clean_screen
from wire600_reserve_last import plan, target_call, validate_change
from wire600_selective_plan import BINDING, digest, validate_files
from wire600_selective_screen import main as repair_screen

OUTPUT = Path('runs/wire600-clean-reproduction')
EXPECTED_REJECTION = 'Native clean-build margin screen fails; no detailed routing'


def require_empty_source():
    if Path('runs/native-stock-screen').exists():
        raise ValueError('Clean reproduction requires an absent source run directory')
    if Path('/tmp/native-source-run.json').exists():
        raise ValueError('Downloaded checkpoint provenance is forbidden in clean reproduction')


def validate_clean_source():
    # Exact bytes, including physical geometry, netlist, constraints, config,
    # measured source gates and state. Never rewrite fresh output to fit a hash.
    validate_files(Path.cwd())
    flow = Path('runs/native-stock-screen/flow')
    if list(flow.glob('*-openroad-detailedrouting')):
        raise ValueError('Detailed routing is forbidden during clean reproduction')
    synthesis = list(flow.glob('*-yosys-synthesis/state_out.json'))
    if len(synthesis) != 1:
        raise ValueError('Missing unique fresh synthesis state')


def main():
    require_empty_source()
    OUTPUT.mkdir(parents=True, exist_ok=False)
    try:
        clean_screen()
    except ValueError as error:
        # This exact control is known to fail electrical reserve gates before
        # the reviewed repairs. Infrastructure failures must never be swallowed.
        if str(error) != EXPECTED_REJECTION:
            raise
    validate_clean_source()
    receipt = dict(clean_synthesis=True, source_artifact_downloaded=False,
                   exact_source_reproduced=True, official_signoff=False,
                   route_authorized=False,
                   files={k: dict(path=v['path'], sha256=digest(v['path']))
                          for k, v in BINDING['files'].items()})
    (OUTPUT/'source_reproduction.json').write_text(json.dumps(receipt, indent=2)+'\n')
    repair_screen(plan_builder=plan, target_emitter=target_call,
                  connectivity_audit=validate_change,
                  output=OUTPUT/'repaired', source_check=validate_clean_source)
    gates = json.loads((OUTPUT/'repaired/gates.json').read_text())
    if not gates['checkpoint_measured_gates_pass']:
        raise ValueError('Fresh repaired reproduction fails measured gates')
    receipt.update(repaired_measured_gates_pass=True,
                   final_state=gates['final_state'], qualified=False,
                   detailed_routing_required=True, exact_netlist_replay_required=True)
    (OUTPUT/'reproduction.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
