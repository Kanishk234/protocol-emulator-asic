"""OpenSTA text evidence, objective interactions and conservative comparisons."""
from collections import Counter, defaultdict
from pathlib import Path
import re
from .evidence import finite, sha, digest

UNITS = {'ns': 1., 'ps': .001, 'us': 1000.}
CATEGORIES = ('placement', 'congestion', 'routing', 'cts', 'setup', 'hold',
              'electrical', 'antenna', 'drc', 'lvs', 'pdn', 'area', 'utilization')
# Collateral effects to measure, never presumed outcomes.
INTERACTIONS = {
 'setup': ['hold', 'electrical', 'congestion', 'area'],
 'hold': ['setup', 'congestion', 'area'],
 'electrical': ['setup', 'hold', 'antenna', 'congestion', 'area'],
 'antenna': ['electrical', 'setup', 'routing', 'drc'],
 'congestion': ['setup', 'hold', 'utilization', 'pdn'],
 'placement': ['congestion', 'cts', 'setup', 'pdn'],
 'routing': ['setup', 'hold', 'antenna', 'drc', 'lvs'],
 'cts': ['setup', 'hold', 'electrical', 'pdn', 'congestion'],
 'drc': ['lvs', 'antenna', 'setup', 'pdn'],
 'lvs': ['drc', 'setup', 'hold'],
 'pdn': ['drc', 'congestion', 'utilization', 'electrical'],
 'area': ['utilization', 'setup', 'congestion'],
 'utilization': ['area', 'congestion', 'pdn', 'setup']}
NUM = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'

def parse_sta(path, stage, corner, unit=None, complete=False):
    path = Path(path)
    text = path.read_text()
    declarations = re.findall(r'(?:Time\s+units?\s*[:=]|time_unit\s*[:=])\s*(\w+)', text, re.I)
    if unit is None:
        unit = declarations[0] if declarations else None
    if unit not in UNITS or any(x != unit for x in declarations):
        raise ValueError('Missing, conflicting or unsupported time units; supply verified --unit')
    if not stage or not corner:
        raise ValueError('Explicit stage and corner required')
    factor = UNITS[unit]
    lines = text.splitlines()
    starts = [i for i, s in enumerate(lines) if s.startswith('Startpoint:')]
    if not starts:
        raise ValueError('No OpenSTA paths')
    paths = []
    for a, b in zip(starts, starts[1:] + [len(lines)]):
        block = lines[a:b]
        def field(label):
            found = [s.split(':', 1)[1].strip() for s in block if s.startswith(label + ':')]
            if len(found) != 1:
                raise ValueError('Missing or ambiguous ' + label)
            return found[0]
        check = {'max': 'setup', 'min': 'hold'}.get(field('Path Type'))
        if check is None:
            raise ValueError('Unsupported path type')
        slack = [(i, re.search(r'(' + NUM + r')\s+slack \((MET|VIOLATED)\)', s))
                 for i, s in enumerate(block) if 'slack (' in s]
        if len(slack) != 1 or slack[0][1] is None:
            raise ValueError('Missing or malformed slack')
        index, m = slack[0]
        value = finite(float(m[1]))
        if (m[2] == 'VIOLATED') != (value < 0):
            raise ValueError('Slack sign contradicts report status')
        transitions = []
        nets = []
        for i, s in enumerate(block):
            transition = re.search(r'([\^v])\s+(\S+)\s+\(([^)]+)\)', s)
            if transition:
                numbers = re.findall(NUM, s[:transition.start()])
                values = list(map(float, numbers))
                transitions.append({'pin': transition[2], 'edge': transition[1],
                    'cell': transition[3], 'raw_columns': values,
                    'delay_ns': values[-2] * factor if len(values) >= 2 else None,
                    'arrival_ns': values[-1] * factor if values else None,
                    'slew_ns': values[-3] * factor if len(values) >= 3 else None,
                    'cap_original': values[-4] if len(values) >= 4 else None,
                    'fanout': values[-5] if len(values) >= 5 else None,
                    'line': a+i+1})
            net = re.search(r'(\S+)\s+\(net\)', s)
            if net:
                nets.append({'name': net[1], 'line': a+i+1})
        def timing(label):
            found = [float(m[1])*factor for s in block
                     if (m := re.search(r'(' + NUM + r')\s+' + label + r'\s*$', s))]
            # OpenSTA repeats arrival with a subtraction sign in the summary.
            return found[0] if found else None
        paths.append({'stage': stage, 'corner': corner, 'check': check,
            'start': field('Startpoint').split(' (')[0],
            'end': field('Endpoint').split(' (')[0], 'group': field('Path Group'),
            'slack_original': value, 'unit': unit, 'slack_ns': value*factor,
            'arrival_ns': timing('data arrival time'), 'required_ns': timing('data required time'),
            'transitions': transitions, 'nets': nets,
            'clock_terms': [{'text': s.strip(), 'line': a+i+1} for i, s in enumerate(block)
                            if any(x in s for x in ['clock uncertainty', 'clock network delay', 'clock reconvergence'])],
            'evidence': {'path': str(path.resolve()), 'sha256': sha(path), 'line': a+index+1}})
    endpoint_slack = defaultdict(list)
    for p in paths:
        endpoint_slack[(p['corner'], p['check'], p['end'])].append(p['slack_ns'])
    return {'paths': paths, 'complete': complete, 'scope': 'reported paths; completeness is caller-attested',
            'tns_ns': sum(min(0, min(v)) for v in endpoint_slack.values()) if complete else None,
            'worst_reported_slack_ns': min(p['slack_ns'] for p in paths),
            'official_signoff': False, 'evidence_id': digest(paths)}

def diagnose(report):
    paths = report['paths']
    launches = Counter(p['start'] for p in paths if p['slack_ns'] < 0)
    shared = Counter(t['pin'] for p in paths if p['slack_ns'] < 0
                     for t in {x['pin']: x for x in p['transitions']}.values())
    return {'evidence_id': report['evidence_id'], 'shared_launches': launches.most_common(),
            'shared_pins': shared.most_common(20), 'unknowns': ['geometry', 'SPEF attribution', 'RTL mapping', 'unreported endpoints'],
            'hypotheses': [{'mechanism': 'shared upstream cone', 'evidence': report['evidence_id'],
                            'falsifier': 'Compare matching ordered paths and net/cell delay across stages; shared membership alone is not causation'}]
                           if launches else [], 'official_signoff': False}

def compare(a, b):
    def key(p):
        return (p['corner'], p['check'], p['start'], p['end'],
                tuple((t['pin'], t['edge']) for t in p['transitions']))
    aa, bb = defaultdict(list), defaultdict(list)
    for p in a['paths']: aa[key(p)].append(p)
    for p in b['paths']: bb[key(p)].append(p)
    result = []
    for k in aa.keys() | bb.keys():
        x, y = aa[k], bb[k]
        state = 'matched' if len(x) == len(y) == 1 else 'ambiguous' if len(x)>1 or len(y)>1 else 'changed_or_missing'
        row = {'start': k[2], 'end': k[3], 'corner': k[0], 'check': k[1], 'status': state}
        if state == 'matched':
            row.update(slack_delta_ns=y[0]['slack_ns']-x[0]['slack_ns'],
                       stages=[x[0]['stage'], y[0]['stage']],
                       evidence=[x[0]['evidence'], y[0]['evidence']])
        result.append(row)
    return {'paths': result, 'tns_delta_ns': None, 'official_signoff': False}

def objectives(observations, limits):
    """Limits are caller-reviewed; no metric can pass on absent evidence."""
    result = {}
    for name, rule in limits.items():
        obs = observations.get(name)
        if not obs or obs.get('value') is None:
            result[name] = 'unknown'
            continue
        if not obs.get('evidence') or obs.get('unit') != rule['unit']:
            raise ValueError('Missing evidence or inconsistent units: ' + name)
        v, threshold = finite(obs['value']), finite(rule['limit'])
        if rule['direction'] not in ('min', 'max'):
            raise ValueError('Invalid limit direction')
        result[name] = 'pass' if (v >= threshold if rule['direction']=='min' else v <= threshold) else 'fail'
    return {'gates': result, 'feasible': bool(result) and all(x=='pass' for x in result.values())}

def pareto(candidates, limits):
    feasible = [c for c in candidates if objectives(c['observations'], limits)['feasible']
                and c.get('correctness') is True and c.get('immutable_constraints') is True]
    def vector(c):
        return [c['observations'][n]['value'] * (-1 if r['direction']=='min' else 1) for n,r in limits.items()]
    return [c['id'] for c in feasible if not any(
        all(x<=y for x,y in zip(vector(d),vector(c))) and any(x<y for x,y in zip(vector(d),vector(c)))
        for d in feasible)]
