"""Independent decoder invocation, with a pinned upstream PS/2 stop-edge fix.

Only the PS/2 subprocess gets the vendor search path. Capture samples and
external protocol timings are never changed to accommodate a decoder.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PS2_VENDOR = ROOT / 'test_internal/vendor/libsigrokdecode_ps2'


def decoder_environment(decoder):
    env = dict(os.environ)
    if any(part.split(':',1)[0] == 'ps2' for part in decoder.split(',')):
        provenance = json.loads((PS2_VENDOR/'PROVENANCE.json').read_text())
        for name, info in provenance['files'].items():
            if hashlib.sha256((PS2_VENDOR/name).read_bytes()).hexdigest() != info['sha256']:
                raise ValueError('Pinned PS/2 decoder source/license changed: '+name)
        env['SIGROKDECODE_DIR'] = str(PS2_VENDOR)
    return env


def decode(vcd, decoder, annotation=None, *, required=False):
    if os.environ.get('TRIPWIRE_SKIP_SIGROK') == '1' or shutil.which('sigrok-cli') is None:
        if required:
            raise RuntimeError('Required independent sigrok decoding unavailable or disabled')
        return None
    command = ['sigrok-cli','-i',str(vcd),'-I','vcd','-P',decoder]
    if annotation:
        command += ['-A',annotation]
    return subprocess.run(command,env=decoder_environment(decoder),
                          capture_output=True,text=True,check=True).stdout
