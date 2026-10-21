"""Single-variable clean control of pre-hold native long-wire buffering.

Keep the rejected delta8 RTL as the control source: only the initial native
wire-length repair target changes. Every measurement/acceptance gate stays fixed.
"""
from native_drop_parallel_screen import configure as control_configure, run_screen
from native_sample_delta8_screen import validate_source


def configure(config):
    result = control_configure(config)
    if result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] != 150:
        raise ValueError('Wrong long-wire control source policy')
    return dict(result, GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=600)


def main():
    validate_source()
    run_screen(config_transform=configure)


if __name__ == '__main__':
    main()
