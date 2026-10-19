"""Test native delay-oriented mapping without a positive global latch slack target."""
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure as wire_configure


def configure(config):
    result = wire_configure(config)
    if result['SYNTH_STRATEGY'] != 'AREA 1' or result['GRT_RESIZER_SETUP_SLACK_MARGIN'] != 0:
        raise ValueError('Unexpected native wire150 mapping baseline')
    result['SYNTH_STRATEGY'] = 'DELAY 0'
    return result


if __name__ == '__main__':
    reserve_screen(config_transform=configure)
