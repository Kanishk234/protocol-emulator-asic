"""Screen the composed resync arithmetic and unit-local staging trial."""
import os
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure


def main():
    if os.environ.get('VARIANT') != 'bs-resync-event-cfg-staging':
        raise ValueError('Expected exact resync/configuration staging RTL trial')
    reserve_screen(config_transform=configure)


if __name__ == '__main__':
    main()
