"""Isolate late long-wire buffering cost, retaining every measured gate."""
from pathlib import Path
from native_posthold_repair_screen import configure as base_configure, main as run_screen


def configure(original):
    result = base_configure(original)
    result['GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH'] = 2000
    return result


def main():
    run_screen(config_transform=configure, output=Path('runs/native-posthold-wire2000'))


if __name__ == '__main__':
    main()
