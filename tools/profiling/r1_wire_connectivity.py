"""Boundary incidence for cell-free leaves; does not replace DRC or GDS LVS."""


def wire_boundary_connected(term):
    net = term.getNet()
    if net is None:
        return False
    if net.getSigType() in ('POWER', 'GROUND'):
        return bool(net.getSWires()) and any(pin.getBoxes() for pin in term.getBPins())
    return len(net.getBTerms()) > 1 and net.getWire() is not None


def apply_unified_patch(source, patch):
    """Apply our single-file text patch with exact positions/context and no fuzz."""
    import re
    lines = source.splitlines(keepends=True)
    edits = patch.splitlines(keepends=True)
    if edits[:2] != ['--- a/disconnected_pins.py\n', '+++ b/disconnected_pins.py\n']:
        raise ValueError('Unexpected checker patch target')
    result = [];cursor = 0;i = 2
    while i < len(edits):
        match = re.fullmatch(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@\n', edits[i])
        if match is None:
            raise ValueError('Malformed checker patch hunk')
        start, old_count, new_start, new_count = map(int, match.groups())
        if start-1 < cursor:
            raise ValueError('Overlapping checker patch hunks')
        result.extend(lines[cursor:start-1]);cursor = start-1
        if len(result) != new_start-1:
            raise ValueError('Checker patch target position differs')
        i += 1;old_seen = new_seen = 0
        while i < len(edits) and not edits[i].startswith('@@ '):
            edit = edits[i];kind = edit[:1];text = edit[1:]
            if kind not in (' ', '+', '-'):
                raise ValueError('Unsupported checker patch line')
            if kind in (' ', '-'):
                if cursor >= len(lines) or lines[cursor] != text:
                    raise ValueError('Checker patch source context differs')
                cursor += 1;old_seen += 1
            if kind in (' ', '+'):
                result.append(text);new_seen += 1
            i += 1
        if (old_seen, new_seen) != (old_count, new_count):
            raise ValueError('Checker patch hunk counts differ')
    result.extend(lines[cursor:])
    return ''.join(result)
