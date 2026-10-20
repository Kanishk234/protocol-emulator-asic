"""Screen one source-bound arithmetic delta with the existing physical policy."""
import os
from native_setup_reserve_screen import main as reserve_screen
from native_wire150_screen import configure

VARIANTS = {'bs-resync-cfg-tx-cursor'}


def main():
    if os.environ.get('VARIANT') not in VARIANTS:
        raise ValueError('Expected a reviewed combined-source arithmetic trial')
    reserve_screen(config_transform=configure)


if __name__ == '__main__':
    main()
