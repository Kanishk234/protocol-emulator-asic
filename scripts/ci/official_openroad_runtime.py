"""Select the already reviewed OpenROAD instrumentation inside one image."""
import os
from pathlib import Path
import sys
import tempfile

from native_route_trace_base import instrument as native_instrument
from wire600_selective_instrument import instrument as selective_instrument


def instrument(text, image, target=None):
    if image == 'tripwire-native-incremental-route:local':
        return native_instrument(text, incremental=True)
    if image == 'tripwire-wire600-selective:local':
        if target is None or not Path(target).is_file():
            raise ValueError('Missing native selective target file')
        return selective_instrument(text, target_path=target)
    raise ValueError('Unknown official runtime repair mode')


def main():
    args = sys.argv[1:]
    image = os.environ.get('LIBRELANE_IMAGE_OVERRIDE')
    if image and args and Path(args[-1]).name == 'rsz_timing_postgrt.tcl':
        text = instrument(Path(args[-1]).read_text(), image,
                          os.environ.get('TRIPWIRE_SELECTIVE_TARGETS'))
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as out:
            out.write(text)
            args[-1] = out.name
    os.execvp('openroad', ['openroad', *args])


if __name__ == '__main__':
    main()
