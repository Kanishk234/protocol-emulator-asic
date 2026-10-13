"""Exact latest-source setup and electrical strength study; fixed-SPEF only."""
from pathlib import Path
import extracted_sizing_sensitivity as base

SOURCE_RUN=38456657314
SOURCE_SHA='e6379fb46a48bcc7c3c0942b30b492fe1a25210c'
NETLIST_SHA='7196cdfa2abbfd5a9f612165618d4c0e03a95744d3532d464047d2fc2f26eb15'
TARGETS={
 '_27477_':('sg13cmos5l_nand2_1','sg13cmos5l_nand2_2'),
 '_27475_':('sg13cmos5l_a21oi_1','sg13cmos5l_a21oi_2'),
 '_24568_':('sg13cmos5l_and3_1','sg13cmos5l_and3_2'),
 '_29456_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2'),
 '_29529_':('sg13cmos5l_nand2_1','sg13cmos5l_nand2_2')}
PAIR={'_27477_':'sg13cmos5l_nand2_2','_27475_':'sg13cmos5l_a21oi_2'}
CASES={'baseline':{},'nand2':{'_27477_':'sg13cmos5l_nand2_2'},
 'a21oi':{'_27475_':'sg13cmos5l_a21oi_2'},'pair':PAIR,
 'pair_and3':dict(PAIR,_24568_='sg13cmos5l_and3_2'),
 'pair_electrical':dict(PAIR,_29456_='sg13cmos5l_nor2_2',_29529_='sg13cmos5l_nand2_2')}


def install_cases():
 base.SOURCE_RUN=SOURCE_RUN;base.SOURCE_SHA=SOURCE_SHA
 base.SOURCE_WORKFLOW='.github/workflows/gds-fanout-load-route.yaml'
 base.SOURCE_DRT_ROOT=Path('runs/fanout-load-route/drt')
 base.NETLIST_SHA=NETLIST_SHA;base.TARGETS=TARGETS;base.CASES=CASES;base.EXTRA_VARIANTS={}

if __name__=='__main__':
 install_cases();base.main(Path('runs/fanout-strength-sensitivity'))
