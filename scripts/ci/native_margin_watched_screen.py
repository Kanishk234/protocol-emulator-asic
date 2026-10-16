"""Run the unchanged native repair policy with quieter Yosys diagnostics."""
from native_margin_screen import configure as margin_configure, main as margin_screen


def configure(config):
    result = margin_configure(config)
    # Pinned pyosys maps WARNING to yosys -q. This changes log verbosity,
    # not the optimization passes or the mapped hardware recipe.
    result['YOSYS_LOG_LEVEL'] = 'WARNING'
    return result


if __name__ == '__main__':
    margin_screen(config_transform=configure)
