"""Read-only authenticated best133 macro boundary, pin and obstruction export.

Uses the preserved OpenDB alone; no placement, repair, routing or timing run.
"""
import json
from pathlib import Path
import subprocess
import cloud_cfg_fanout as cfg
from cloud_hold_allocation import EXPECTED

ROOT = cfg.ROOT
SOURCE = ROOT / 'build/reset_combined'
OUT = ROOT / 'build/boundary_audit'
SCRIPT = r'''
read_db $::env(WARP_INPUT_ODB)
set block [ord::get_db_block]
set macro [$block findInst u_fabric]
if {$macro == "NULL" || [$macro getOrient] ne "R0"} {error "Expected R0 macro missing"}
set out [open $::env(WARP_GEOMETRY) w]
puts $out "DBU\t[$block getDbUnitsPerMicron]"
proc rect_record {out prefix box} {
    puts $out [join [concat $prefix [list [$box xMin] [$box yMin] [$box xMax] [$box yMax]]] "\t"]
}
foreach inst [$block getInsts] {
    rect_record $out [list CELL [$inst getName] [[$inst getMaster] getName]] [$inst getBBox]
    foreach term [$inst getITerms] {
        set net [$term getNet]
        if {$net == "NULL" || [$net getSigType] in {POWER GROUND}} {continue}
        foreach geometry [$term getGeometries] {
            lassign $geometry layer rect
            rect_record $out [list PIN [$inst getName] [[$term getMTerm] getName] [$net getName] [$layer getName]] $rect
        }
    }
}
foreach term [$block getBTerms] {
    set net [$term getNet]
    if {$net == "NULL" || [$net getSigType] in {POWER GROUND}} {continue}
    foreach pin [$term getBPins] {
        foreach box [$pin getBoxes] {
            rect_record $out [list BOUNDARY [$term getName] [$net getName] [[$box getTechLayer] getName]] $box
        }
    }
}
# Master coordinates remain explicitly local; R0 translation is the saved origin.
lassign [$macro getOrigin] mx my
puts $out "MACRO_ORIGIN\t$mx\t$my\tR0"
foreach box [[$macro getMaster] getObstructions] {
    rect_record $out [list MACRO_OBS_LOCAL [[$box getTechLayer] getName]] $box
}
foreach obs [$block getObstructions] {
    set box [$obs getBBox]
    rect_record $out [list BLOCK_OBS [[$box getTechLayer] getName]] $box
}
close $out
# DEF retains track declarations, actual rows, top pins and special-wire geometry.
write_def $::env(WARP_DEF)
puts "Boundary export complete; no placement or routing executed"
'''


def authenticate():
    for name, digest in EXPECTED.items():
        if cfg.sha(SOURCE / name) != digest:
            raise ValueError('Producer view differs: ' + name)


def summarize(path):
    counts = {}
    macro_pins = 0
    for line in path.read_text().splitlines():
        fields = line.split('\t')
        counts[fields[0]] = counts.get(fields[0], 0) + 1
        if fields[:2] == ['PIN', 'u_fabric']:
            macro_pins += 1
    if counts.get('CELL') != 3606 or counts.get('MACRO_ORIGIN') != 1:
        raise ValueError('Incomplete native instance census')
    if macro_pins == 0 or counts.get('MACRO_OBS_LOCAL', 0) < 4 or not counts.get('BOUNDARY'):
        raise ValueError('Missing boundary pins or macro obstructions')
    return {'record_counts': counts, 'macro_pin_rectangles': macro_pins}


def main():
    OUT.mkdir(exist_ok=False)
    result = {'observation_complete': False, 'physical_acceptance': False,
              'source_run': 38167697696, 'source_sha256': EXPECTED,
              'scope': 'read-only geometry; no new routing/timing acceptance'}
    try:
        authenticate()
        script = OUT / 'export.tcl'
        script.write_text(SCRIPT)
        geometry = OUT / 'geometry.tsv'
        env = {'WARP_INPUT_ODB': SOURCE / 'padded.odb',
               'WARP_GEOMETRY': geometry, 'WARP_DEF': OUT / 'source.def'}
        cmd = ['docker', 'run', '--rm', '-v', f'{ROOT}:{ROOT}', '-w', str(ROOT)]
        for key, value in env.items():
            cmd.extend(['-e', f'{key}={value}'])
        cmd.extend(['--entrypoint', 'openroad', cfg.IMAGE, '-exit', str(script)])
        with (OUT / 'export.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        result.update(summarize(geometry))
        authenticate()
        result['source_unchanged'] = True
        result['exports_sha256'] = {name: cfg.sha(OUT / name) for name in ('geometry.tsv', 'source.def', 'export.tcl')}
        result['observation_complete'] = True
    except Exception as exc:
        result['error'] = str(exc)
        raise
    finally:
        (OUT / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
