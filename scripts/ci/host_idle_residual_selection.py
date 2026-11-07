"""Select bounded data reroutes from actual native segments, never guide overlap alone."""
from copy import deepcopy
from c_select_congestion_readback import crossing_nets


def validate_orientations(plan):
    for item in plan['diodes']:
        if item.get('locked_orientation') not in ('R0', 'MX', 'MY', 'R180'):
            raise ValueError('Expected native OpenDB orientation, not DEF orientation')


def scoped_plan(plan, scope):
    if scope not in ('full', 'net15518_only', 'omit_net15518'):
        raise ValueError('Unreviewed routing isolation scope')
    result = deepcopy(plan)
    if scope != 'full':
        keep_target = scope == 'net15518_only'
        result['diodes'] = [d for d in result['diodes'] if (d['net']=='net15518') == keep_target]
        result['allowed_signal_nets_to_reroute'] = [d['net'] for d in result['diodes']]
        if keep_target:
            result['congestion_signal_nets'] = []
            result['residual_edges'] = []
    result['isolation_scope'] = scope
    return result


def select(routes, edges, eligible):
    selected = []
    for edge in crossing_nets(routes, deepcopy(edges)):
        candidates = [name for name in edge['crossing_route_names']
                      if name in eligible and name not in selected]
        if not candidates:
            raise ValueError('Residual edge has no distinct eligible signal crossing')
        selected.append(min(candidates, key=lambda n: (eligible[n], len(routes[n]), n)))
    return selected
