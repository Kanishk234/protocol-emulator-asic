"""Exclude weak A22OI mapping on the exact verified cache-only source."""
import hashlib
import json
from pathlib import Path

BASE = ['sg13cmos5l_buf_1', 'sg13cmos5l_nand2_1', 'sg13cmos5l_nor3_1']
EXCLUDED = BASE + ['sg13cmos5l_a22oi_1']
EVIDENCE = Path(__file__).resolve().parents[2] / 'spikes/phase2_stock_flow/level_cache_no_owner'


def prepare(root, evidence=EVIDENCE):
    root, evidence = Path(root), Path(evidence)
    manifest = json.loads((evidence / 'candidate.json').read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    inventory = lambda: {p.name: digest(p) for p in (root/'src').iterdir() if p.suffix in ('.v', '.vh')}
    before = inventory()
    path = root/'src/config.json'
    if digest(path) != manifest['reference_config_sha256'] or before != manifest['candidate_rtl_inventory']:
        raise ValueError('Wrong exact cache-only source/config')
    config = json.loads(path.read_text())
    selected_path = root/'spikes/phase2_stock_flow/selected_profile.json'
    selected = json.loads(selected_path.read_text())
    if selected['profile'] != 'portable_cpad_drive2_tx_pending_level_cache_no_owner':
        raise ValueError('Wrong cache-only profile')
    if config['EXTRA_EXCLUDED_CELLS'] != BASE or config['CLOCK_PERIOD'] != 20:
        raise ValueError('Unexpected baseline gates/clock')
    config['EXTRA_EXCLUDED_CELLS'] = EXCLUDED
    blob = json.dumps(config, indent=2)+'\n'
    sha = hashlib.sha256(blob.encode()).hexdigest()
    selected.update(profile='portable_cache_no_a22oi', config_sha256=sha,
                    comparison_reference_run=43957277296,
                    comparison_reference_config_sha256=manifest['reference_config_sha256'],
                    additional_changes_from_reference={'EXTRA_EXCLUDED_CELLS': EXCLUDED},
                    same_rtl_as_reference=True)
    selected['changes']['EXTRA_EXCLUDED_CELLS'] = EXCLUDED
    path.write_text(blob)
    selected_path.write_text(json.dumps(selected, indent=2)+'\n')
    assert inventory() == before
    receipt = dict(source_run=43957277296, source_config_sha256=manifest['reference_config_sha256'],
                   candidate_config_sha256=sha, changed_fields=['EXTRA_EXCLUDED_CELLS'],
                   rtl_hashes=before, excluded=EXCLUDED, physical_qualified=False,
                   official_signoff=False)
    out = root/'runs/cache-gate-profile'
    out.mkdir(parents=True, exist_ok=True)
    (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    print(json.dumps(prepare(Path.cwd()), indent=2))
