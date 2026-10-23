"""Insert exact identity-buffer edits inside tracked native timing repair."""
import os
from pathlib import Path
import re
import sys
import tempfile

from native_route_trace_base import instrument as native_instrument


def instrument(text, target_path=None):
    result = native_instrument(text, incremental=True)
    anchor = 'estimate_parasitics -global_routing\n'
    if result.count(anchor) != 1:
        raise ValueError('Ambiguous native selective insertion')
    # Do not seed estimator caches before direct ODB connectivity edits. A
    # second estimate does not necessarily clear invalid incremental state.
    # Finish edit routing first, estimate once, then retain the native timing
    # repair's independent incremental-routing interval.
    edits = '''global_route -start_incremental
write_verilog $::env(STEP_DIR)/selective.before.v
source /usr/local/share/tripwire/electrical_repair.tcl
source /usr/local/share/tripwire/incremental_placement.tcl
set selective_frozen [tripwire_freeze_existing_placement]
source /usr/local/share/tripwire/wire600_selective_targets.tcl
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
tripwire_restore_placement_status $selective_frozen
write_verilog $::env(STEP_DIR)/selective.after.v
global_route -end_incremental
'''
    marker = 'puts "TRIPWIRE_SELECTIVE repaired and refreshed; native timing repair follows"\n'
    if target_path is not None:
        target_path = str(target_path)
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+', target_path):
            raise ValueError('Unsafe native selective target path')
        edits = edits.replace('source /usr/local/share/tripwire/wire600_selective_targets.tcl',
                              'source {'+target_path+'}')
    return result.replace(anchor, edits + anchor + marker, 1)


def main():
    args = sys.argv[1:]
    if args and Path(args[-1]).name == 'rsz_timing_postgrt.tcl':
        text = instrument(Path(args[-1]).read_text())
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as f:
            f.write(text)
            args[-1] = f.name
    os.execvp('openroad', ['openroad', *args])


if __name__ == '__main__':
    main()
