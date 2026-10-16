"""Hosted native GCD API regression for the explicitly patched OpenROAD.

Routing commands follow pinned OpenROAD gcd.tcl (BSD-3-Clause). This proves
only the exercised API behavior, never chip routing/contention/timing closure.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

import cloud_cfg_fanout as cfg
from audit_native_grid import guide_coverage
from cloud_fanout_grt import parse_congestion

ROOT = cfg.ROOT
REV = 'dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
FIXTURES = {
    'gcd.def': ('src/grt/test/gcd.def', 'a76daa31656bcb9682071392b39e285d06a0a8eb88d4f84962f9479c84a98074'),
    'Nangate45.lef': ('test/Nangate45/Nangate45.lef', 'caa4e9b45e081f93720ce2c4d581497321ddc6fbcb1ffe1b384e324bbd5d43a7'),
}
MARKER = 'WARP_REGRESSION_FORCE_BEGIN'


def segments(text):
    """Strict Manhattan native routing map, independent of IHP layer names."""
    lines = text.splitlines()
    nets, index = {}, 0
    while index < len(lines):
        name = lines[index].replace('\\', '')
        if not name or name in nets or index+1 >= len(lines) or lines[index+1] != '(':
            raise ValueError('Malformed/duplicate native net header')
        index += 2
        route = []
        while index < len(lines) and lines[index] != ')':
            fields = lines[index].split()
            if len(fields) != 6 or not all(re.fullmatch(r'metal(?:[1-9]|10)', fields[i]) for i in (2, 5)):
                raise ValueError('Invalid Nangate native segment')
            x0, y0, x1, y1 = (int(fields[i]) for i in (0, 1, 3, 4))
            if (x0 != x1 and y0 != y1) or (fields[2] != fields[5] and (x0 != x1 or y0 != y1)):
                raise ValueError('Non-Manhattan/cross-layer planar segment')
            a, b = (x0, y0, fields[2]), (x1, y1, fields[5])
            route.append(tuple(sorted((a, b))))
            index += 1
        if index >= len(lines) or not route:
            raise ValueError('Incomplete/empty native route')
        nets[name] = tuple(sorted(route))
        index += 1
    if not nets:
        raise ValueError('Empty native route map')
    return nets


def selected_names(path):
    rows = Path(path).read_text().splitlines()
    if len(rows) != 2 or any(not row.startswith('SELECTED\t') for row in rows):
        raise ValueError('Expected two actual selected names')
    names = [row.split('\t', 1)[1].replace('\\', '') for row in rows]
    if len(set(names)) != 2 or any(not name or re.search(r'clk|clock', name, re.I) for name in names):
        raise ValueError('Invalid selected signal census')
    return names


def zero_table(text):
    rows = parse_congestion(text)
    if any(row[key] for row in rows for key in ('total_overflow', 'max_h_overflow', 'max_v_overflow')):
        raise ValueError('Native regression route has overflow')
    return rows


def validate(stock, custom):
    stock, custom = Path(stock), Path(custom)
    stock_text = (stock/'before-segments.txt').read_text()
    initial_text = (custom/'before-segments.txt').read_text()
    before = segments(initial_text)
    if stock_text != initial_text or segments(stock_text) != before:
        raise ValueError('Stock/custom default native segments differ')
    for suffix in ('census.tsv', 'guides.tsv'):
        if (stock/('before-'+suffix)).read_bytes() != (custom/('before-'+suffix)).read_bytes():
            raise ValueError('Stock/custom default physical or guide census differs')
    zero_table((stock/'native.log').read_text())
    raw = (custom/'native.log').read_text()
    if raw.count(MARKER) != 1 or raw.count('WARP_REGRESSION_FORCE_COMPLETE') != 1:
        raise ValueError('Missing/repeated actual repair witnesses')
    head, tail = raw.split(MARKER, 1)
    zero_table(head)
    final_table = zero_table(tail)
    if re.findall(r'\[INFO GRT-0009\] rerouting (\d+) nets\.', tail) != ['2']:
        raise ValueError('Expected exactly one native two-net reroute witness')
    rows = (custom/'invalid-cases.tsv').read_text().splitlines()
    if rows != ['INVALID\tduplicate\tREJECTED', 'INVALID\tnull\tREJECTED', 'INVALID\tclock\tREJECTED']:
        raise ValueError('Actual invalid-case census incomplete or duplicated')
    for case in ('duplicate', 'null', 'clock'):
        for kind in ('segments.txt', 'census.tsv', 'guides.tsv'):
            if (custom/f'{case}-{kind}').read_bytes() != (custom/f'before-{kind}').read_bytes():
                raise ValueError('Invalid call mutated routing/physical state: '+case)
    after = segments((custom/'after-segments.txt').read_text())
    selected = selected_names(custom/'selected.tsv')
    if set(before) != set(after) or not set(selected) <= set(before):
        raise ValueError('Final full native route census changed')
    changed = [name for name in before if before[name] != after[name]]
    if set(changed)-set(selected):
        raise ValueError('Unselected native routes changed')
    census = (custom/'before-census.tsv').read_bytes()
    if census != (custom/'after-census.tsv').read_bytes():
        raise ValueError('Physical instance/connectivity census changed')
    coverage = guide_coverage(custom/'after-guides.tsv', census.decode())
    if coverage['missing_guides']:
        raise ValueError('Final native guides incomplete')
    return {'passed': True, 'scope': 'Noncongested GCD unchanged-net API regression only',
            'actual_case_counts': {'default_tools': 2, 'invalid_rejections': 3, 'forced_pair': 1},
            'selected_names': selected, 'selected_routes_changed': sorted(changed),
            'complete_native_route_count': len(before), 'unselected_routes_identical': True,
            'physical_census_identical': True, 'guide_coverage': coverage, 'final_native_table': final_table,
            'default_segments_sha256': hashlib.sha256(stock_text.encode()).hexdigest(),
            'physical_acceptance': False}


def fetch_fixture(directory):
    for name, (remote, expected) in FIXTURES.items():
        path = directory/name
        with urllib.request.urlopen(f'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{REV}/{remote}', timeout=45) as response:
            path.write_bytes(response.read())
        if cfg.sha(path) != expected:
            raise ValueError('Pinned native fixture hash mismatch: '+name)
    for name, remote in [('OpenROAD-LICENSE', 'LICENSE'), ('upstream-gcd.tcl', 'src/grt/test/gcd.tcl')]:
        with urllib.request.urlopen(f'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{REV}/{remote}', timeout=45) as response:
            (directory/name).write_bytes(response.read())
    (directory/'ATTRIBUTION.md').write_text('Untouched OpenROAD fixtures at '+REV+'; routing commands follow src/grt/test/gcd.tcl. BSD-3-Clause; retain OpenROAD-LICENSE and original file notices. Nangate45 LEF remains untouched with original attribution.\n')


def tool_paths(path):
    paths = Path(path).read_text().splitlines()
    if len(paths) != 2 or any(not re.fullmatch(r'/nix/store/[a-z0-9]{32}-[^/]+', p) for p in paths):
        raise ValueError('Expected exactly stock/custom pinned Nix output paths')
    result = [Path(p)/'bin/openroad' for p in paths]
    if any(not p.is_file() for p in result) or result[0] == result[1]:
        raise ValueError('Missing or identical native stock/custom tools')
    return result


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise ValueError('Native tool regressions run only on hosted runners')
    output = ROOT/'build/router_regression'
    output.mkdir(exist_ok=False)
    report = {'passed': False, 'physical_acceptance': False,
              'source_revision': os.environ.get('GITHUB_SHA'), 'workflow_run': os.environ.get('GITHUB_RUN_ID'),
              'workflow_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'), 'upstream_revision': REV}
    try:
        fixture = output/'fixture'; fixture.mkdir()
        fetch_fixture(fixture)
        census_script = output/'census.tcl'; census_script.write_text(cfg.CENSUS)
        manifest = Path(os.environ.get('WARP_ROUTER_TOOL_PATHS', str(ROOT/'build/force_build/tool-paths.txt')))
        binaries = tool_paths(manifest)
        report['tool_manifest_sha256'] = cfg.sha(manifest)
        report['tools'] = [{'path': str(p), 'sha256': cfg.sha(p)} for p in binaries]
        report['fixtures'] = {p.name: cfg.sha(p) for p in fixture.iterdir() if p.is_file()}
        script = ROOT/'tools/router_build/regression.tcl'
        report['script_sha256'] = cfg.sha(script)
        report['patch_sha256'] = cfg.sha(ROOT/'patches/openroad_force_reroute.patch')
        for mode, binary in zip(('stock', 'custom'), binaries):
            directory = output/mode; directory.mkdir()
            env = dict(os.environ, WARP_REGRESSION_LEF=str(fixture/'Nangate45.lef'),
                       WARP_REGRESSION_DEF=str(fixture/'gcd.def'), WARP_REGRESSION_CENSUS=str(census_script),
                       WARP_REGRESSION_OUT=str(directory), WARP_REGRESSION_MODE=mode)
            with (directory/'native.log').open('w') as log:
                process = subprocess.run([str(binary), '-exit', str(script)], env=env, stdout=log,
                                         stderr=subprocess.STDOUT, timeout=180, cwd=ROOT)
            report[mode+'_returncode'] = process.returncode
            if process.returncode != 0:
                raise ValueError('Native '+mode+' regression failed; inspect retained native.log')
        report.update(validate(output/'stock', output/'custom'))
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        (output/'result.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
