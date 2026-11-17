"""Configure native late antenna repair and audit fresh database netlist views."""
import hashlib
import json
from pathlib import Path
import re
import shutil

from event_nor2_screen import validate_antenna_only_changes
from postgrt_timing import CORNERS

BASE_SHA = '155c0c8efe5375f12cd34feb5d4a559c860d2f94970be7d2bf150fbb50b6e9af'
SUBSTITUTIONS = {'+OpenROAD.ResizerTimingPostGRT': 'OpenROAD.RepairAntennas',
                 '+OpenROAD.RepairAntennas-1': 'OpenROAD.GlobalRouting'}


def one(root, pattern):
    rows = list(Path(root).glob(pattern))
    if len(rows) != 1:
        raise ValueError('Missing/ambiguous native evidence: '+pattern)
    return rows[0]


def prepare(root, *, final_full_route=True):
    root = Path(root)
    path = root/'src/config.json'
    before = path.read_bytes()
    if hashlib.sha256(before).hexdigest() != BASE_SHA:
        raise ValueError('Wrong exact A22OI exclusion configuration')
    config = json.loads(before)
    if config.get('meta', {}).get('substituting_steps'):
        raise ValueError('Unexpected existing flow customization')
    if config['CLOCK_PERIOD'] != 20:
        raise ValueError('Wrong source clock')
    p = root/'spikes/phase2_stock_flow/selected_profile.json'
    selected = json.loads(p.read_text())
    if selected['profile'] != 'portable_cache_no_a22oi':
        raise ValueError('Wrong mapping source')
    substitutions=SUBSTITUTIONS if final_full_route else dict(list(SUBSTITUTIONS.items())[:1])
    config['meta'] = {**config.get('meta', {'version': 1, 'flow': 'Classic'}), 'substituting_steps': substitutions}
    config['GRT_ALLOW_CONGESTION'] = False
    blob = json.dumps(config, indent=2)+'\n'
    sha = hashlib.sha256(blob.encode()).hexdigest()
    selected.update(profile='portable_cache_native_post_antenna' if final_full_route else 'portable_cache_native_final_antenna', config_sha256=sha,
                    comparison_reference_run=43972384723,
                    comparison_reference_config_sha256=BASE_SHA,
                    additional_changes_from_reference={'meta.substituting_steps': substitutions,
                                                       'GRT_ALLOW_CONGESTION': False},
                    native_post_antenna=True, native_final_antenna=not final_full_route, stock_sequence=False)
    selected['changes']['GRT_ALLOW_CONGESTION'] = False
    path.write_text(blob)
    p.write_text(json.dumps(selected, indent=2)+'\n')
    out=root/'runs/cache-post-antenna'
    out.mkdir(parents=True,exist_ok=True)
    receipt=dict(reference_run=43972384723, reference_config_sha256=BASE_SHA,
                 candidate_config_sha256=sha, native_substitutions=substitutions, final_full_global_route=final_full_route,
                 congestion_allowed=False, physical_qualified=False, official_signoff=False)
    (out/'recipe.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


def native_chain(physical, source, *, final_full_route=True):
    physical, source = Path(physical), Path(source)
    timing = one(physical, '*-openroad-resizertimingpostgrt/state_out.json')
    antenna = one(physical, '*-openroad-repairantennas-1/state_out.json')
    original = one(physical, '*-openroad-stamidpnr-3/state_out.json')
    old, ant, final = [json.loads(p.read_text()) for p in (timing, antenna, original)]
    before = json.loads((antenna.parent/'state_in.json').read_text())
    if before['odb'] != old['odb']:
        raise ValueError('Native repair is not directly after final timing')
    if final_full_route:
        routing = one(physical, '*-openroad-globalrouting-1/state_out.json')
        routed=json.loads(routing.read_text())
        route_in=json.loads((routing.parent/'state_in.json').read_text())
        if route_in['odb']!=ant['odb'] or final['odb']!=routed['odb']:
            raise ValueError('Final route/repair database chain differs')
    elif list(physical.glob('*-openroad-globalrouting-1')) or final['odb']!=ant['odb']:
        raise ValueError('Final antenna policy has an unexpected later route/database')
    current = json.loads(source.read_text())
    if any(current[k] != final[k] for k in ('odb', 'def', 'sdc')):
        raise ValueError('Audit is not the final repaired database')
    config=json.loads((physical/'resolved.json').read_text())
    if config.get('GRT_ALLOW_CONGESTION') is not False:
        raise ValueError('Native final repair must reject congestion')
    log=one(antenna.parent,'*-openroad-diodeinsertion/openroad-diodeinsertion.log').read_text()
    commands=re.findall(r'^\+ repair_antennas\b[^\n]*',log,re.M)
    if len(commands)!=1 or '-allow_congestion' in commands[0] or '-diode_only' not in commands[0]:
        raise ValueError('Wrong final native antenna command')
    if final_full_route:
        route_log=one(routing.parent,'openroad-globalrouting*.log').read_text()
        route_commands=re.findall(r'^\+ global_route\b[^\n]*',route_log,re.M)
        if len(route_commands)!=1 or '-allow_congestion' in route_commands[0]:
            raise ValueError('Wrong final native global-routing command')
    return old, final, antenna


def readbacks(physical, source, audit, *, final_full_route=True):
    old, final, antenna = native_chain(physical, source, final_full_route=final_full_route)
    exports=[]
    for corner in CORNERS:
        for phase in ('before','after'):
            stage=one(Path(audit)/f'{phase}-{corner}','*-openroad-stamidpnr')
            state=json.loads((stage/'state_in.json').read_text())
            if state['odb']!=final['odb']:
                raise ValueError('Readback used wrong physical database')
            nl,pnl=stage/'native_antenna.nl.v',stage/'native_antenna.pnl.v'
            if not nl.is_file() or not pnl.is_file():
                raise ValueError('Missing fresh database netlist exports')
            validate_antenna_only_changes(Path(old['nl']).read_text(),nl.read_text())
            exports.append((nl,pnl))
    if any(n.read_bytes()!=exports[0][0].read_bytes() or p.read_bytes()!=exports[0][1].read_bytes() for n,p in exports):
        raise ValueError('Repeated/corner database exports differ')
    return final,exports[0],antenna


def promote(physical, source, audit, *, final_full_route=True):
    final,(nl,pnl),_ = readbacks(physical,source,audit,final_full_route=final_full_route)
    source=Path(source)
    fresh={}
    for key,p in (('nl',nl),('pnl',pnl)):
        target=source.parent/f'audited.{key}.v'
        shutil.copy2(p,target)
        fresh[key]=str(target.resolve())
    state={**final,**fresh,'spef':None,'sdf':None,'lib':None,'metrics':{}}
    out=source.with_name('audited_state.json')
    out.write_text(json.dumps(state,indent=2)+'\n')
    return out


def validate_final(physical, source, audit, *, final_full_route=True):
    _,(nl,pnl),antenna=readbacks(physical,source,audit,final_full_route=final_full_route)
    state=json.loads(Path(source).read_text())
    for key,p in (('nl',nl),('pnl',pnl)):
        if Path(state[key]).read_bytes()!=p.read_bytes():
            raise ValueError('Qualification netlist is not fresh ODB readback')
    return dict(native_post_timing_antenna_repair=True,
                native_repair_congestion_disallowed=True,
                native_final_global_route_verified=final_full_route,
                final_antenna_is_last_physical_step=not final_full_route,
                final_native_repair_state=str(antenna),
                existing_logic_and_connections_preserved=True,
                fresh_netlist_readbacks_verified=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final-antenna',action='store_true')
    args=parser.parse_args()
    print(json.dumps(prepare(Path.cwd(),final_full_route=not args.final_antenna),indent=2))
