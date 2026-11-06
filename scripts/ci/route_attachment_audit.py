"""Only two reviewed local Via1 attachments may augment frozen source routes."""
import hashlib
import json

from route_segment_audit import parse

REVIEWED = [('_02001_', [939600, 313200]),
            ('u_chip.g_lane[1].ot[26]', [586800, 226800])]


def canonical(name):
    return name.replace('\\[', '[').replace('\\]', ']')


def validate_plan(attachments):
    assert [(a['net'], a['point_dbu']) for a in attachments] == REVIEWED
    for item in attachments:
        assert set(item) == {'net', 'point_dbu'}
        assert all(type(v) is int and v % 7200 == 3600 for v in item['point_dbu'])


def atomic_routes(routes):
    """Canonical grid edges retain multiplicity while allowing segment splits."""
    result = {}
    for name, segments in routes.items():
        edges = []
        for a, b in segments:
            if a[2] != b[2]:
                assert a[:2] == b[:2]
                lo, hi = sorted((int(a[2].removeprefix('Metal')), int(b[2].removeprefix('Metal'))))
                edges.extend(((a[0], a[1], f'Metal{i}'), (a[0], a[1], f'Metal{i+1}'))
                             for i in range(lo, hi))
            else:
                axis = 0 if a[0] != b[0] else 1
                lo, hi = sorted((a[axis], b[axis]))
                assert hi > lo and (hi-lo) % 7200 == 0
                for point in range(lo, hi, 7200):
                    start, end = list(a), list(a)
                    start[axis], end[axis] = point, point+7200
                    edges.append((tuple(start), tuple(end)))
        result[name] = sorted(edges)
    return result


def verify_loaded(text, reference, attachments):
    validate_plan(attachments)
    routes = {name: list(segments) for name, segments in parse(text).items()}
    for item in attachments:
        names = [n for n in routes if canonical(n) == item['net']]
        assert len(names) == 1
        segments = routes[names[0]]
        x, y = item['point_dbu']
        via = tuple(sorted(((x, y, 'Metal1'), (x, y, 'Metal2'))))
        assert segments.count(via) == 1, 'Missing or repeated reviewed attachment'
        segments.remove(via)
        assert any(a[2] == b[2] == 'Metal2' and
                   min(a[0], b[0]) <= x <= max(a[0], b[0]) and
                   min(a[1], b[1]) <= y <= max(a[1], b[1])
                   for a, b in segments), 'Attachment misses original Metal2 route'
    encoded = json.dumps(atomic_routes(routes), sort_keys=True, separators=(',', ':'))
    assert hashlib.sha256(encoded.encode()).hexdigest() == reference['atomic_route_sha256'], 'Original route changed beyond reviewed vias'


def add_guides(database, attachments):
    import odb
    validate_plan(attachments)
    block = database.getChip().getBlock()
    grid = block.getGCellGrid()
    assert grid is not None
    for points in (list(grid.getGridX()), list(grid.getGridY())):
        assert len(points) > 2 and all(b-a == 7200 for a, b in zip(points, points[1:]))
    tech = database.getTech()
    lower, upper = tech.findLayer('Metal1'), tech.findLayer('Metal2')
    assert lower.getRoutingLevel() == 1 and upper.getRoutingLevel() == 2
    for item in attachments:
        nets = [n for n in block.getNets() if canonical(n.getName()) == item['net']]
        assert len(nets) == 1 and not nets[0].isSpecial()
        x, y = item['point_dbu']
        guide = odb.dbGuide.create(nets[0], lower, upper,
                                   odb.Rect(x-3600, y-3600, x+3600, y+3600), False)
        assert guide is not None, 'Failed to add reviewed Via1 guide'
