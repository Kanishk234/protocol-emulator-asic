"""Exact remaining setup-path strength study; fixed-SPEF diagnostic only."""
from pathlib import Path
import extracted_sizing_sensitivity as base

SOURCE_RUN=38515215944
SOURCE_SHA='ad0f3ec1fa2bf66341ca79ef00df6f51a09b0066'
NETLIST_SHA='d2d3cf49c3d7d62da9c7ad794e02c82d657e3277cef9e4d68bb061eabd6216c0'
TARGETS={'_24896_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2'),
         '_24568_':('sg13cmos5l_and3_1','sg13cmos5l_and3_2')}
CASES={'baseline':{},'nor2':{'_24896_':'sg13cmos5l_nor2_2'},
       'and3':{'_24568_':'sg13cmos5l_and3_2'},
       'pair':{'_24896_':'sg13cmos5l_nor2_2','_24568_':'sg13cmos5l_and3_2'}}


def install_cases():
    base.SOURCE_RUN=SOURCE_RUN;base.SOURCE_SHA=SOURCE_SHA
    base.SOURCE_WORKFLOW='.github/workflows/gds-hold-electrical-route.yaml'
    base.SOURCE_DRT_ROOT=Path('runs/hold-electrical-route/drt')
    base.NETLIST_SHA=NETLIST_SHA;base.TARGETS=TARGETS;base.CASES=CASES;base.EXTRA_VARIANTS={}

if __name__=='__main__':
    install_cases();base.main(Path('runs/final_setup_sensitivity'))
