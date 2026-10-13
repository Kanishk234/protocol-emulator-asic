import hashlib
from pathlib import Path
import pytest
import combined_physical_plan as planner


def fixture(tmp_path,monkeypatch):
    cells=[];nets=[];hold=[]
    def cell(name,master):
        cells.append((name,master));return name
    for name in planner.SETUP:cell(name,planner.TARGETS[name][0])
    for i in range(19):
        driver=cell(f'hdriver{i}','sg13cmos5l_buf_1');sink=cell(f'hflop{i}','sg13cmos5l_dfrbpq_1')
        nets.append((f'hnet{i}',[(driver,'X'),(sink,'D')]))
        hold.append(f'Startpoint: hdriver{i}\nEndpoint: hflop{i} (rising edge-triggered flip-flop clocked by clk)\n 0.02 slack (MET)\n')
    for i in range(29):
        driver=cell(f'edriver{i}','sg13cmos5l_buf_1');sink=cell(f'esink{i}','sg13cmos5l_buf_1')
        nets.append((f'enet{i}',[(driver,'X'),(sink,'A')]))
    component='\n'.join(f'- {n} {m} + PLACED ( {260000+i*4800} 241920 ) N ;' for i,(n,m) in enumerate(cells))
    layout='UNITS DISTANCE MICRONS 1000 ;\nROW row CoreSite 260000 241920 N DO 2000 BY 1 STEP 480 0 ;\nCOMPONENTS '+str(len(cells))+' ;\n'+component+'\nEND COMPONENTS\nNETS '+str(len(nets))+' ;\n'+'\n'.join('- '+n+' '+' '.join('( '+a+' '+p+' )' for a,p in pins)+' ;' for n,pins in nets)+'\nEND NETS'
    netlist='\n'.join(m+' '+n+' (.A(a), .X(x));' for n,m in cells)
    report='nom_fast_1p32V_m40C\n'+''.join(hold)
    checks={c:c+'\nmax slew\n'+''.join(f'edriver{i}/X 1 2 -1 (VIOLATED)\n' for i in range(29))+'max fanout\nmax capacitance\n' for c in ('nom_fast_1p32V_m40C','nom_typ_1p20V_25C','nom_slow_1p08V_125C')}
    std=tmp_path/'std.lef';std.write_text('fixture');macro=tmp_path/'macro.lef';macro.write_text('fixture')
    digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
    for key,value in [('NL_SHA',digest(netlist)),('DEF_SHA',digest(layout)),('REPORT_SHA',digest(report)),('MACRO_LEF_SHA',digest('fixture'))]:monkeypatch.setattr(planner,key,value)
    monkeypatch.setattr(planner,'CHECKS_SHA',{c:digest(s) for c,s in checks.items()})
    def occupancy(text,lef,units,instance,master):
        return (2400,3780),[(n,260000+i*4800,241920,262400+i*4800,245700) for i,(n,m) in enumerate(cells) if n!=instance]
    monkeypatch.setattr(planner,'occupancy',occupancy)
    return netlist,layout,report,checks,std,macro


def test_all_repairs_allocate_together_and_preserve_source_partition(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch);p=planner.plan(*args)
    assert len(p['resizes'])==8 and p['hold_delay_cells']==19 and p['electrical_target_nets']==29
    assert p['added_buffers']==48 and p['footprint_overlap_count']==0
    assert p['physical_change_applied'] is False
    assert all(g['rail_source']!='u_chip.u_sram.sram' for g in p['groups'])
    pins=[tuple(pin) for g in p['groups'] for pin in g['sinks']]
    assert len(pins)==len(set(pins))
    assert all(pin not in ('CLK','RESET_B','GATE') for name,pin in pins)
    tcl=planner.target_call(args[1],p)
    assert tcl.index('tripwire_size_electrical')<tcl.index('tripwire_freeze_existing_placement')<tcl.index('tripwire_electrical_repair')


@pytest.mark.parametrize('fault',['netlist','layout','hold','checks','macro'])
def test_wrong_source_or_evidence_rejected(tmp_path,monkeypatch,fault):
    args=list(fixture(tmp_path,monkeypatch))
    if fault in ('netlist','layout','hold'):args[{'netlist':0,'layout':1,'hold':2}[fault]]+='changed'
    elif fault=='checks':args[3][next(iter(args[3]))]+='changed'
    else:args[5].write_text('changed')
    with pytest.raises(ValueError):planner.plan(*args)


def test_tcl_refuses_unreviewed_resize_or_source(tmp_path,monkeypatch):
    args=fixture(tmp_path,monkeypatch);p=planner.plan(*args)
    p['resizes'][0]['new_master']='sg13cmos5l_inv_1'
    with pytest.raises(ValueError):planner.target_call(args[1],p)
    with pytest.raises(ValueError):planner.target_call(args[1]+'changed',p)


def test_macro_rails_cannot_anchor_standard_cell_power():
    loc={'u_chip.u_sram.sram':('RM_IHPSG13_1P_512x16_c2_bm_bist',0,0,'FS'),'driver':('sg13cmos5l_buf_1',0,0,'N')}
    assert planner.standard_anchor([('u_chip.u_sram.sram','A_MEN'),('driver','X')],loc)=='driver'
    with pytest.raises(ValueError):planner.standard_anchor([('u_chip.u_sram.sram','A_DOUT[5]')],loc)
