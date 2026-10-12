"""Read-only final DEF load inventory; no physical repair or signoff claim."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def inventory(layout, checks):
    components = layout.split('COMPONENTS ', 1)[1].split('END COMPONENTS', 1)[0]
    masters = {n: m for n, m in re.findall(r'^\s*- (\S+) (\S+)', components, re.M)}
    section = layout.split('\nNETS ', 1)[1].split('END NETS', 1)[0]
    attached = {}
    for entry in section.split(';'):
        hit = re.search(r'^\s*- (\S+)', entry)
        if not hit: continue
        net = hit[1]
        for name, pin in re.findall(r'\(\s*(\S+)\s+(\S+)\s*\)', entry.split(' + ', 1)[0]):
            key = (name, pin)
            if key in attached: raise ValueError('Pin attached to multiple nets')
            attached[key] = net
    by_net = {}
    for pin, net in attached.items(): by_net.setdefault(net, []).append(pin)
    rows = re.findall(r'^\s*(\S+)/(\S+)\s+8\s+(\d+)[^\n]*\(VIOLATED\)', checks, re.M)
    if not rows: raise ValueError('Missing fanout failures')
    drivers = []
    for name, pin, reported in rows:
        net = attached[(name, pin)]
        sinks = sorted(p for p in by_net[net] if p != (name, pin))
        if len(sinks) != int(reported): raise ValueError('DEF/report load count mismatch')
        clock = name.startswith('clkbuf_')
        if clock and any(p != 'A' or masters[n] != 'sg13cmos5l_buf_8' for n, p in sinks):
            raise ValueError('Unreviewed clock topology')
        if not clock and any(p in ('CLK', 'GCLK', 'GATE', 'RESET_B') for n, p in sinks):
            raise ValueError('Data split contains clock/reset sinks')
        budget = 8 if clock else 6
        options = [(k, keep) for k in range(1, 9) for keep in range(budget + 1)
                   if keep + k <= budget and 0 < len(sinks) - keep <= budget * k]
        k, keep = min(options, key=lambda v: (v[0], -v[1]))
        drivers.append(dict(instance=name, pin=pin, master=masters[name], net=net,
            loads=len(sinks), antenna_loads=sum(masters[n]=='sg13cmos5l_antennanp' for n,p in sinks),
            clock_branch=clock, retained_loads=keep, proposed_buffers=k,
            group_load_budget=budget, sinks=sinks))
    ren = ('u_chip.u_sram.sram', 'A_REN')
    # DEF escapes hierarchy names differently across exporters; require one semantic suffix.
    candidates = [p for p in attached if p[1]=='A_REN']
    if len(candidates) != 1: raise ValueError('Missing unique SRAM REN')
    ren = candidates[0]; net = attached[ren]
    drivers_ren = [p for p in by_net[net] if p[1] in ('X','Y','Q')]
    if len(drivers_ren) != 1: raise ValueError('Missing unique REN driver')
    return dict(def_sha256=hashlib.sha256(layout.encode()).hexdigest(),
        drivers=drivers, proposed_fanout_buffers=sum(d['proposed_buffers'] for d in drivers),
        ren=dict(pin=ren, net=net, driver=drivers_ren[0], master=masters[drivers_ren[0][0]]),
        legal_sites_verified=False, physical_change_applied=False, official_signoff=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('layout', type=Path); parser.add_argument('checks', type=Path)
    args = parser.parse_args()
    print(json.dumps(inventory(args.layout.read_text(), args.checks.read_text()), indent=2))
