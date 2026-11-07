"""Select bounded data reroutes from actual native segments, never guide overlap alone."""
from copy import deepcopy
from c_select_congestion_readback import crossing_nets


def validate_orientations(plan):
    for item in plan['diodes']:
        if item.get('locked_orientation') not in ('R0', 'MX', 'MY', 'R180'):
            raise ValueError('Expected native OpenDB orientation, not DEF orientation')


def select(routes, edges, eligible):
    selected = []
    for edge in crossing_nets(routes, deepcopy(edges)):
        candidates = [name for name in edge['crossing_route_names']
                      if name in eligible and name not in selected]
        if not candidates:
            raise ValueError('Residual edge has no distinct eligible signal crossing')
        selected.append(min(candidates, key=lambda n: (eligible[n], len(routes[n]), n)))
    return selected
