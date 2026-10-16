"""Test shorter native data-wire segments with the measured CTS spacing."""
from native_clockspacing_screen import configure as clock_configure
from native_margin_screen import main as margin_screen


def configure(config):
    result = clock_configure(config)
    result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 100
    return result


if __name__ == '__main__':
    margin_screen(config_transform=configure)
