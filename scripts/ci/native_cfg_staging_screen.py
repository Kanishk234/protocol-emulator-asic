"""Screen unit-local configuration staging against the measured event-late baseline."""
import os
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure


def main():
    if os.environ.get('VARIANT') != 'bs-event-cfg-staging':
        raise ValueError('Expected exact configuration staging RTL trial')
    reserve_screen(config_transform=configure)


if __name__ == '__main__':
    main()
