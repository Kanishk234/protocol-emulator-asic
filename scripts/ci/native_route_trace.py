"""Read-only instrumentation of the exact pinned timing-repair Tcl script."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile

SCRIPT_SHA256 = '17a7b1f4a7bce58cd2e33f6b7fc4a9a822a3332cee8901216184897e437ddec3'
STAGES = ('initial_route', 'timing_repair', 'placement', 'final_route')


def instrument(text, incremental=False):
    if hashlib.sha256(text.encode()).hexdigest() != SCRIPT_SHA256:
        raise ValueError('Unexpected pinned native timing script')
    preamble = '''
proc tripwire_route_snapshot {stage} {
    set root [file join $::env(STEP_DIR) route_trace $stage]
    file mkdir $root
    write_db [file join $root snapshot.odb]
    write_def [file join $root snapshot.def]
    write_verilog [file join $root snapshot.v]
    if {$stage eq "initial_route" || $stage eq "final_route"} {
        file copy $::env(STEP_DIR)/after_grt.guide [file join $root after_grt.guide]
    }
    puts "TRIPWIRE_ROUTE_SNAPSHOT $stage"
}
'''
    # Insert observations only; retain every original native command and option.
    first = 'source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\n# }'
    text = text.replace(first, first.replace('\n# }',
                        '\ntripwire_route_snapshot initial_route\n# }'), 1)
    placement = 'source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl'
    text = text.replace(placement,
        'tripwire_route_snapshot timing_repair\n'+placement+
        '\ntripwire_route_snapshot placement', 1)
    final = '    source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\n}'
    text = text.replace(final, final.replace('\n}',
                        '\n    tripwire_route_snapshot final_route\n}'), 1)
    if incremental:
        # Track native setup/hold repair and DPL, not just newly inserted cells.
        # The initial full GRT remains unchanged and initializes all routes.
        anchor = 'estimate_parasitics -global_routing\n'
        final_route = '    source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl\n'
        if text.count(anchor) != 1 or text.count(final_route) != 1:
            raise ValueError('Ambiguous incremental route instrumentation')
        text = text.replace(anchor, anchor+'global_route -start_incremental\n'
                            'puts "TRIPWIRE_INCREMENTAL begin"\n', 1)
        text = text.replace(final_route,
            '    global_route -end_incremental\n'
            '    puts "TRIPWIRE_INCREMENTAL end"\n'
            '    write_guide $::env(STEP_DIR)/after_grt.guide\n', 1)
    return preamble + text


def main():
    args = sys.argv[1:]
    if args and Path(args[-1]).name == 'rsz_timing_postgrt.tcl':
        mode = os.environ.get('TRIPWIRE_ROUTE_MODE', 'trace')
        if mode not in ('trace', 'incremental'):
            raise ValueError('Unknown route control mode')
        patched = instrument(Path(args[-1]).read_text(), incremental=mode == 'incremental')
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tcl', delete=False) as out:
            out.write(patched)
            args[-1] = out.name
    os.execvp('openroad', ['openroad', *args])


if __name__ == '__main__':
    main()
