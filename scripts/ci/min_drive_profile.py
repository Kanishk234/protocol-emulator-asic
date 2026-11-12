"""Prepare one native cell-exclusion trial from the exact C-pad hold125 recipe."""
import argparse
import hashlib
import json
from pathlib import Path

BASE_SHA = '4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7'
EXCLUDED = ['sg13cmos5l_buf_1', 'sg13cmos5l_nand2_1', 'sg13cmos5l_nor3_1']


def prepare(root):
    root = Path(root)
    path = root/'src/config.json'
    before = path.read_bytes()
    if hashlib.sha256(before).hexdigest() != BASE_SHA:
        raise ValueError('Wrong source hold125 configuration')
    config = json.loads(before)
    if config['EXTRA_EXCLUDED_CELLS'] != EXCLUDED[:1]:
        raise ValueError('Unexpected baseline exclusions')
    selected_path = root/'spikes/phase2_stock_flow/selected_profile.json'
    selected = json.loads(selected_path.read_text())
    if selected.get('variant') != 'clock75_hold125' or selected.get('c_pad_decode') is not True:
        raise ValueError('Wrong C-pad source profile')
    config['EXTRA_EXCLUDED_CELLS'] = EXCLUDED
    blob = (json.dumps(config, indent=2)+'\n').encode()
    digest = hashlib.sha256(blob).hexdigest()
    selected.update(profile='portable_cpad_drive2', config_sha256=digest,
                    comparison_reference_run=42964952931, comparison_reference_artifact_id=13833267530,
                    comparison_reference_config_sha256=BASE_SHA,
                    additional_changes_from_reference={'EXTRA_EXCLUDED_CELLS': EXCLUDED})
    selected['changes']['EXTRA_EXCLUDED_CELLS'] = EXCLUDED
    path.write_bytes(blob)
    selected_path.write_text(json.dumps(selected, indent=2)+'\n')
    receipt = dict(reference_config_sha256=BASE_SHA, candidate_config_sha256=digest,
                   changed_fields=['EXTRA_EXCLUDED_CELLS'], excluded=EXCLUDED,
                   physical_qualified=False, official_gds_signoff=False)
    out = root/'runs/min-drive'
    out.mkdir(parents=True, exist_ok=True)
    (out/'profile.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    print(json.dumps(prepare(parser.parse_args().root), indent=2))
