"""Measure cached fabric selection under the unchanged native screen policy."""
import os
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure


def main():
    if os.environ.get('VARIANT') != 'bs-resync-cfg-tx-cached-select':
        raise ValueError('Expected exact cached fabric selection variant')
    reserve_screen(config_transform=configure)


if __name__ == '__main__':
    main()
