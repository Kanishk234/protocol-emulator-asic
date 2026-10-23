"""Explicit native execution backend for the official-flow plugin container.

Existing diagnostic jobs retain their original Docker command lines. Native
execution requires the dedicated image marker, not just an environment flag.
"""
import os
from pathlib import Path
import subprocess

MARKER = Path('/usr/local/share/tripwire/official-runtime-v1')
IMAGES = {
    'tripwire-native-incremental-route:local': 'Dockerfile.openroad-native-incremental',
    'tripwire-wire600-selective:local': 'Dockerfile.openroad-wire600-selective',
}


def native():
    value = os.environ.get('TRIPWIRE_NATIVE_RUNTIME', '0')
    if value not in ('0', '1'):
        raise ValueError('Unknown physical runtime')
    if value == '1' and (not MARKER.is_file() or MARKER.read_text().strip() != '3.1.0.dev3'):
        raise ValueError('Native physical runtime requires the reviewed container')
    return value == '1'


def container_flags():
    return [] if native() else ['--docker-no-tty', '--dockerized']


def prepare_image(image, dockerfile):
    if image not in IMAGES or Path(dockerfile).name != IMAGES[image]:
        raise ValueError('Unreviewed physical backend image')
    if native():
        if image == 'tripwire-wire600-selective:local':
            target = Path(dockerfile).with_name('wire600_selective_targets.tcl').resolve()
            if not target.is_file():
                raise ValueError('Missing reviewed selective targets')
            os.environ['TRIPWIRE_SELECTIVE_TARGETS'] = str(target)
        return
    subprocess.run(['docker', 'build', '-t', image, '-f', str(dockerfile),
                    str(Path(dockerfile).parent)], check=True)
