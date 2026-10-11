"""One receiver-local reset placement policy with bounded same-row redistribution."""
import json
import os
from pathlib import Path

import cloud_cfg_fanout as cfg
import cloud_hotspot_padding as producer

ROOT = cfg.ROOT
INPUT = ROOT/'build/reset643_input'
OUT = ROOT/'build/reset643_whitespace'
PLAN = json.loads((Path(__file__).with_name('reset643_plan.json')).read_text())
SETUP = producer.EDIT.split('set selected {}', 1)[0]
FINISH = producer.EDIT.split('census ${::env(WARP_AFTER)}.canonical', 1)[1]


def edit():
    script = SETUP + '\nset out [open $::env(WARP_SELECTION) w]\n'
    for name, move in PLAN.items():
        left, bottom, right, top = move['before']
        x, y, end, upper = move['after']
        script += f'''
set name {{{name}}}
set inst [$block findInst $name]
if {{$inst eq "NULL" || [$inst getPlacementStatus] ne "PLACED"}} {{error "Missing movable planned cell"}}
set box [$inst getBBox]
if {{[$box xMin] != {left} || [$box yMin] != {bottom} || [$box xMax] != {right} || [$box yMax] != {top}}} {{error "Actual source geometry differs"}}
if {{({x}-{left})%480 != 0 || ({y}-{bottom})%7560 != 0}} {{error "Site or power phase differs"}}
$inst setLocation {x} {y}
set box [$inst getBBox]
if {{[$box xMin] != {x} || [$box yMin] != {y} || [$box xMax] != {end} || [$box yMax] != {upper}}} {{error "Native target box differs"}}
puts $out $name
'''
    return script + 'close $out\ncensus ${::env(WARP_AFTER)}.canonical\n' + FINISH


def audit_move(before, after, geometry_before, geometry_after, selected):
    old, opins = cfg.parse_census(before)
    new, npins = cfg.parse_census(after)
    dbu, site, boxes = producer.boxes(geometry_before)
    ndu, nsite, final = producer.boxes(geometry_after)
    if set(old) != set(new) or len(old) != 3606 or opins != npins or (dbu,site,ndu,nsite) != (1000,480,1000,480) or set(selected) != set(PLAN) or len(selected) != len(PLAN):
        raise ValueError('Scope/connectivity/units differ')
    endpoints = {k[1]: v for k,v in opins.items() if k[0]=='PIN' and v[-1].replace('\\','')=='net643'}
    if endpoints != {'u_shell.u_crc._329_/RESET_B':['INPUT','SIGNAL','net643'],
                     'u_shell.u_crc._329__644/L_HI':['OUTPUT','SIGNAL','net643']}:
        raise ValueError('Exact receiver-local reset endpoints differ')
    for name in old:
        if old[name][0] != new[name][0] or old[name][2:] != new[name][2:]:
            raise ValueError('Master/orientation/status changed: '+name)
        if name in PLAN:
            if boxes[name] != ('CORE',tuple(PLAN[name]['before'])) or final[name] != ('CORE',tuple(PLAN[name]['after'])):
                raise ValueError('Exact bounded placement plan differs: '+name)
        elif old[name] != new[name] or boxes[name] != final[name]:
            raise ValueError('Unplanned movement: '+name)
    return {'changed_instances':sorted(PLAN), 'plan':PLAN, 'all_other_instances_exact':True,
            'connectivity_masters_orientations_status_exact':True, 'redistributed_row_bottom_dbu':468720,
            'other_row_shift_dbu':1920, 'tie_vertical_rows':-16, 'power_phase_preserved':True,
            'reset_net643_endpoints':endpoints, 'scope':'Copied placement; routing improvement unproven'}


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true': raise ValueError('Native execution is cloud-only')
    producer.INPUT, producer.OUT = INPUT, OUT
    producer.EDIT, producer.audit_placement = edit(), audit_move
    try:
        producer.main()
    finally:
        path=OUT/'result.json'
        if path.exists():
            result=json.loads(path.read_text())
            result['scope']='receiver-local net643 tie with bounded same-row redistribution'
            path.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__': main()
