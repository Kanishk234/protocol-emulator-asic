"""Screen the verified resync/event RTL combination with the native wire150 policy."""
import os
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure


def main():
    if os.environ.get('VARIANT') != 'bs-resync-event':
        raise ValueError('Expected exact resync/event RTL trial')
    reserve_screen(config_transform=configure)


if __name__ == '__main__':
    main()
