"""Insert four combinational identity LUTs before the first UART receive FF.

Keep its clock, set control, output and primitive unchanged. Pin the FF to the
qualified X6Y1/C site; nextpnr must route actual buffer resources. No delay
statements or timing exceptions are introduced. Delay benefit is unmeasured.
"""
import copy


def buffer_uart_rx(design):
    derived=copy.deepcopy(design);m=derived['modules']['warp_top']
    sync=m['netnames']['u_user.u_uart.g_prims.u_rx.sync']['bits']
    reset=m['netnames']['u_user.rst_n']['bits']
    if len(sync)!=2 or len(reset)!=1 or any(type(b) is not int for b in sync+reset):
        raise ValueError('Require the existing UART synchronizer and reset nets')
    drivers=[(n,c) for n,c in m['cells'].items()
             if c.get('port_directions',{}).get('O')=='output' and c['connections'].get('O')==sync[:1]]
    if len(drivers)!=1:raise ValueError('Ambiguous first UART synchronizer driver')
    name,cell=drivers[0]
    if (cell['type']!='LUTFF_SS' or cell['parameters'] or
            set(cell['connections'])!={'CLK','D','O','S'} or
            any(len(v)!=1 or type(v[0]) is not int for v in cell['connections'].values())):
        raise ValueError('Unsupported UART synchronizer primitive or pin shape')
    if (any(n.startswith('wp_uart_rx_delay_') for n in m['cells']) or
            any(k in cell['attributes'] for k in ('NEXTPNR_BEL','BEL_STRENGTH'))):
        raise ValueError('UART delay or placement constraint already exists')
    used=[b for c in m['cells'].values() for v in c['connections'].values() for b in v if type(b) is int]
    used += [b for n in m['netnames'].values() for b in n['bits'] if type(b) is int]
    used += [b for p in m.get('ports',{}).values() for b in p['bits'] if type(b) is int]
    fresh=max(used)+1;before=copy.deepcopy(cell);signal=list(cell['connections']['D']);chain=[]
    for index in range(4):
        lutname='wp_uart_rx_delay_'+str(index);out=[fresh+index]
        lut=dict(type='LUT4',hide_name=0,parameters={'INIT':'1010101010101010'},attributes={},
            port_directions={'I0':'input','I1':'input','I2':'input','I3':'input','O':'output'},
            connections={'I0':signal,'I1':list(reset),'I2':list(reset),'I3':list(reset),'O':out})
        m['cells'][lutname]=lut;m['netnames'][lutname]={'hide_name':0,'bits':out,'attributes':{}}
        chain.append(dict(name=lutname,cell=copy.deepcopy(lut)));signal=out
    cell['connections']['D']=signal
    # The packer deletes the FF after merging it into the last LUT. Constrain
    # that retained cell, not the temporary FF that would leave a stale binding.
    m['cells']['wp_uart_rx_delay_3']['attributes'].update(
        NEXTPNR_BEL='X6Y1/C',BEL_STRENGTH=format(6,'032b'))
    chain[-1]['cell']=copy.deepcopy(m['cells']['wp_uart_rx_delay_3'])
    return derived,dict(ff=name,before=before,after=copy.deepcopy(cell),chain=chain,
        logical_buffer_luts=4,required_capture_bel='X6Y1/C',expected_packed_capture_cell='wp_uart_rx_delay_3',
        scope='Binary data identity with unchanged FF primitive/clock/set/output. Physical delay, fit and native/reload/timing require measurement.')
