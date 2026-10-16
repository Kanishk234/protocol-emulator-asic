"""Test native CTS buffer spacing on the measured wire200 clean recipe."""
from native_margin_wire_screen import configure as wire_configure
from native_margin_screen import main as margin_screen


def configure(config):
    result = wire_configure(config)
    result['CTS_DISTANCE_BETWEEN_BUFFERS'] = 100
    return result


if __name__ == '__main__':
    margin_screen(config_transform=configure)
