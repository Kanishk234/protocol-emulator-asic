"""Read-only targeted STA on the immutable C-pad extracted checkpoint."""
import hashlib
import json
from pathlib import Path

from official_dev4_cpad_route import verify_source, bootstrap_ciel_antenna
from extracted_sizing_sensitivity import sta_input_state, corner_metrics, baseline_matches
from native_stock_route import run_step


def main():
    source, config = verify_source()
    bootstrap_ciel_antenna(config, source, output_name='cpad-audit-pdk')
    root = Path('runs/extracted-timing')
    state_path = root / '11-openroad-stapostpnr/state_out.json'
    state = json.loads(state_path.read_text())
    identity = json.loads((root / 'constraint_identity.json').read_text())
    sdc = Path(identity['sta_constraint_file'])
    assert hashlib.sha256(sdc.read_bytes()).hexdigest() == identity['sha256']
    assert sdc.read_bytes() == Path('src/signoff.sdc').read_bytes()
    paths = [Path(state[k]) for k in ('nl', 'odb')] + [sdc]
    paths += [Path(p) for p in state['spef'].values()]
    def hashes():
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    assert hashlib.sha256(Path(state["nl"]).read_bytes()).hexdigest() == '3bf46dca904b867b0c9c5a7ddd7e508d3c7e5ec0ac03d637d0262277a61b8639'
    before = hashes()
    config.update(SIGNOFF_SDC_FILE=str(sdc.resolve()),
                  STA_EXTRA_CORNER_TCL_FILE=str(Path('scripts/ci/cpad_endpoint_audit.tcl').resolve()))
    out = Path('runs/cpad-endpoint-audit')
    out.mkdir(exist_ok=False)
    checkpoint = out / 'input.json'
    checkpoint.write_text(json.dumps(sta_input_state(state, Path(state['nl'])), indent=2)+'\n')
    run_step(config, checkpoint, out/'sta', ['OpenROAD.STAPostPNR'])
    stage = next((out/'sta').glob('*-openroad-stapostpnr/state_out.json')).parent
    measured = corner_metrics(stage)
    baseline_matches(measured, json.loads((root/'corner_summary.json').read_text()))
    assert hashes() == before, 'Read-only endpoint audit changed source views'
    (out/'receipt.json').write_text(json.dumps(dict(source_run=43063738642,
        source_hashes=before, baseline_reproduced=True, physical_repairs=False,
        official_signoff=False, corners=measured), indent=2)+'\n')


if __name__ == '__main__':
    main()
