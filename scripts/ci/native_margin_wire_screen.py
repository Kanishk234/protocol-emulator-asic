"""Test a positive native wire-repair limit on the clean margin recipe."""
from native_margin_watched_screen import configure as watched_configure
from native_margin_screen import main as margin_screen


def configure(config):
    result = watched_configure(config)
    # Compare against the measured zero-length/no-edit repair step.
    # This is a physical experiment, not a claim that all failures are caused
    # by the zero limit or that clock fanout will be repaired by this setting.
    result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 200
    return result


if __name__ == '__main__':
    margin_screen(config_transform=configure)
