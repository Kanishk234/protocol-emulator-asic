"""Check source-buffer synthesis preservation and report native retention."""
from pathlib import Path
from event_nor2_screen import logical_cells


def inspect_netlists(synthesis, final, variant):
    if variant not in ('constants','all_words'):
        raise ValueError('Unreviewed enable-drive audit')
    words=range(48,52) if variant=='constants' else range(52)
    expected={f'u_chip.g_lane[{lane}].u_slots.g_word[{word}].g_enable_drive.u_buf'
              for lane in range(2) for word in words}
    def cells(text):
        raw=logical_cells(text);result={n.lstrip('\\'):v for n,v in raw.items()}
        if len(result)!=len(raw):raise ValueError('Ambiguous cell spelling')
        return result
    first,last=cells(synthesis),cells(final)
    actual={n for n in first if '.g_enable_drive.u_buf' in n}
    if actual!=expected or any(first[n][0]!='sg13cmos5l_buf_4' for n in expected):
        raise ValueError('Synthesis did not retain reviewed enable-drive buffers')
    retained={n:last[n][0] for n in sorted(expected) if n in last}
    return dict(variant=variant,source_buffer_count=len(expected),
                synthesis_source_buffers_preserved=True,final_retained_buffer_count=len(retained),
                final_retained_masters=retained,removed_by_native_optimization=sorted(expected-set(retained)),
                physical_qualification_performed=False)


def audit(root, variant):
    root=Path(root)
    def one(pattern):
        paths=list(root.glob(pattern))
        if len(paths)!=1:raise ValueError('Missing unique mapped netlist: '+pattern)
        return paths[0].read_text()
    return inspect_netlists(one('*-yosys-synthesis/tt_um_tripwire.nl.v'),
                            one('*-openroad-resizertimingpostgrt/tt_um_tripwire.nl.v'),variant)
