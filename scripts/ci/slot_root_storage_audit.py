"""Audit the selected constant-bank refinement, without signoff claims."""
from pathlib import Path
import re
from event_nor2_screen import logical_cells


def inspect_netlists(synthesis, final):
    first,last=logical_cells(synthesis),logical_cells(final)
    def gates(cells):
        result={}
        for name,(master,pins) in cells.items():
            normalized=name.replace('\\','')
            match=re.search(r'u_chip\.g_lane\[(\d+)\]\.u_slots\.g_word\[(\d+)\].*\.u_icg$',normalized)
            if match:
                key=tuple(map(int,match.groups()))
                if key in result:raise ValueError('Duplicate word clock gate')
                result[key]=master
        return result
    expected={(lane,word) for lane in range(2) for word in range(48)}
    original=gates(first)
    if set(original)!=expected or any(m!='sg13cmos5l_lgcp_1' for m in original.values()):
        raise ValueError('Synthesis did not exercise the reviewed constant-bank storage refinement')
    def constant_outputs(cells):
        rows=[]
        for name,(master,pins) in cells.items():
            values=dict(pins)
            for pin,value in pins:
                net=re.sub(r'\s+','',value.replace('\\',''))
                direct=re.fullmatch(r'u_chip\.g_lane\[([01])\]\.(?:kk|u_slots\.k)\[(\d+)\]',net)
                word=re.fullmatch(r'u_chip\.g_lane\[([01])\]\.u_slots\.g_word\[(\d+)\]\.mem\[(\d+)\]',net)
                key=None
                if direct and int(direct[2])<64:key=(int(direct[1]),int(direct[2]))
                if word and 48<=int(word[2])<52 and int(word[3])<16:
                    key=(int(word[1]),(int(word[2])-48)*16+int(word[3]))
                if pin in ('Q','Q_N','X','Y') and key is not None:
                    rows.append(dict(instance=name,master=master,pin=pin,net=net,lane=key[0],constant_bit=key[1],
                                     clock=re.sub(r'\s+','',values.get('CLK','').replace('\\',''))))
        return rows
    synthesis_drivers=constant_outputs(first)
    if (len(synthesis_drivers)!=128 or len({(r['lane'],r['constant_bit']) for r in synthesis_drivers})!=128
            or any(not r['master'].startswith('sg13cmos5l_df') or r['clock']!='clk' for r in synthesis_drivers)):
        raise ValueError('Constant storage is not128root-clock flip-flops after synthesis')
    return dict(source_slot_clock_gates=len(original),expected_source_slot_clock_gates=96,
                removed_constant_bank_clock_gates=8,
                synthesis_constant_output_drivers=synthesis_drivers,
                final_slot_clock_gates=len(gates(last)),final_constant_output_drivers=constant_outputs(last),
                physical_qualification_performed=False)


def audit(root):
    root=Path(root)
    def one(pattern):
        files=list(root.glob(pattern))
        if len(files)!=1:raise ValueError('Missing unique netlist: '+pattern)
        return files[0].read_text()
    return inspect_netlists(one('*-yosys-synthesis/tt_um_tripwire.nl.v'),
                            one('*-openroad-resizertimingpostgrt/tt_um_tripwire.nl.v'))
