"""One stock density control on the functionally verified selector RTL."""
import hashlib
import json
from pathlib import Path

BASE_CONFIG_SHA = '4d71243f672fac34f004c43a8c8bfc46cffaae2b2929f7d3c788de1fac72a9f7'
CONFIG_SHA = '2b822640c55c227b4b5e881421b5e4e863c92c050b4c6c3578dd28d92ae11dfc'
SELECTOR_SHA = '55b90c37d0c786cca1d40db523ddc6406e8c021a0d654a97dbc5f1a9dcbab614'


def encoded(config):
    return json.dumps(config, indent=2) + '\n'


def select(config):
    before = hashlib.sha256(encoded(config).encode()).hexdigest()
    if before != BASE_CONFIG_SHA or config.get('PL_TARGET_DENSITY_PCT') != 56:
        raise ValueError('Wrong selector comparison configuration')
    result = dict(config, PL_TARGET_DENSITY_PCT=60)
    if hashlib.sha256(encoded(result).encode()).hexdigest() != CONFIG_SHA:
        raise ValueError('Unexpected density trial configuration')
    return result


def prepare(root):
    config_path = root / 'src/config.json'
    target = root / 'src/trw_pin_cfg.v'
    if hashlib.sha256(target.read_bytes()).hexdigest() != SELECTOR_SHA:
        raise ValueError('Wrong selector source for density control')
    receipt_path = root / 'spikes/phase2_stock_flow/selected_profile.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('config_sha256') != BASE_CONFIG_SHA:
        raise ValueError('Wrong density comparison profile')
    result = select(json.loads(config_path.read_text()))
    receipt.update(config_sha256=CONFIG_SHA, density_comparison_run=43951998125,
                   density_only_change=dict(before=56, after=60), hardware_unchanged=True)
    receipt['changes']['PL_TARGET_DENSITY_PCT'] = 60
    config_path.write_text(encoded(result))
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')


if __name__ == '__main__':
    prepare(Path.cwd())
