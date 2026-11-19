"""Strict GDS record preservation and context-name collision checks for R1."""
import hashlib
import struct


def record(kind, datatype=0, payload=b''):
    if len(payload) % 2:
        payload += b'\0'
    return struct.pack('>HBB', len(payload)+4, kind, datatype)+payload


def string(kind, value):
    return record(kind, 6, value.encode('ascii'))


def records(data):
    offset = 0
    while offset < len(data):
        if offset+4 > len(data):
            raise ValueError('Truncated GDS record header')
        size, kind, datatype = struct.unpack('>HBB', data[offset:offset+4])
        if size < 4 or size % 2 or offset+size > len(data):
            raise ValueError('Invalid GDS record length')
        raw = data[offset:offset+size]; offset += size
        yield kind, datatype, raw


def text(raw):
    return raw[4:].rstrip(b'\0').decode('ascii')


def library(data):
    header = []; cells = {}; current = None; name = None; units = []; ended = False
    for kind, datatype, raw in records(data):
        if ended:
            raise ValueError('Data after GDS ENDLIB')
        if kind == 5:
            if current is not None:
                raise ValueError('Nested GDS structure')
            current = []; name = None
        if current is not None:
            current.append(raw)
            if kind == 6:
                if name is not None or datatype != 6:
                    raise ValueError('Duplicate or malformed GDS STRNAME')
                name = text(raw)
            if kind == 7:
                if not name or name in cells:
                    raise ValueError('Missing or duplicate GDS structure name')
                cells[name] = b''.join(current); current = None
        elif kind == 4:
            ended = True
        elif not cells:
            header.append(raw)
            if kind == 3:
                units.append(raw)
        else:
            raise ValueError('Unexpected GDS data between structures')
    if not ended or current is not None or len(units) != 1 or not cells:
        raise ValueError('Incomplete GDS library')
    references = {text(r) for cell in cells.values() for k, d, r in records(cell) if k == 18}
    if not references <= cells.keys():
        raise ValueError('Unresolved GDS structure reference')
    return b''.join(header), units[0], cells


def fingerprint(cell):
    # Structure timestamps differ between independent exports. Every geometry,
    # reference, property, ordering and name byte must otherwise be identical.
    return hashlib.sha256(b''.join(r for k, d, r in records(cell) if k != 5)).hexdigest()


def merge_contexts(inputs):
    cells = {}; shared = {}; context_cells = {}; header = None; units = None
    for case, source, target, data in inputs:
        h, u, imported = library(data)
        if source not in imported or target in cells or target in imported:
            raise ValueError('Missing source or conflicting context master')
        if units is not None and u != units:
            raise ValueError('GDS units differ between contexts')
        header, units = h if header is None else header, u
        renamed = []
        for name, cell in imported.items():
            if any(k == 18 and text(r) == source for k,d,r in records(cell)):
                raise ValueError('Context master referenced inside leaf library')
            if name == source:
                renamed = [string(6,target) if k == 6 else r for k,d,r in records(cell)]
                continue
            digest = fingerprint(cell)
            if name in shared and shared[name] != digest:
                raise ValueError('Shared GDS structure has different geometry: '+name)
            if name in context_cells:
                raise ValueError('Shared/context master name collision')
            shared[name] = digest; cells.setdefault(name, cell)
        cells[target] = b''.join(renamed); context_cells[target] = case
    if not cells:
        raise ValueError('No context GDS inputs')
    return header, cells, shared


def labels(cell):
    active = None
    for kind, datatype, raw in records(cell):
        if kind == 12:
            if active is not None:
                raise ValueError('Nested GDS TEXT element')
            active = []
        if active is not None:
            active.append(raw)
            if kind == 17:
                strings = [text(r) for k,d,r in records(b''.join(active)) if k == 25]
                if len(strings) != 1:
                    raise ValueError('Malformed GDS pin text')
                yield strings[0], active
                active = None


def translated_label(element, name, origin):
    result = []; xy_count = 0
    for kind, datatype, raw in records(b''.join(element)):
        if kind == 16:
            if datatype != 3 or len(raw) != 12:
                raise ValueError('Unexpected GDS TEXT position')
            x,y = struct.unpack('>ii',raw[4:]); xy_count += 1
            result.append(record(16,3,struct.pack('>ii',x+origin[0],y+origin[1])))
        elif kind == 25:
            result.append(string(25,name))
        else:
            result.append(raw)
    if xy_count != 1:
        raise ValueError('Missing GDS pin label position')
    return b''.join(result)


def top_structure(name, placements, width, height, pin_labels):
    # Deterministic valid GDS dates: creation and modification, 2000-01-01.
    dates = struct.pack('>12h',*(2000,1,1,0,0,0)*2)
    result = [record(5,2,dates),string(6,name)]
    for instance in placements:
        result.extend((record(10),string(18,instance['planned_master']),
                       record(16,3,struct.pack('>ii',*instance['origin_dbu'])),record(17)))
    result.extend(pin_labels)
    result.extend((record(8),record(13,2,struct.pack('>h',189)),
                   record(14,2,struct.pack('>h',4)),
                   record(16,3,struct.pack('>10i',0,0,width,0,width,height,0,height,0,0)),
                   record(17),record(7)))
    return b''.join(result)
