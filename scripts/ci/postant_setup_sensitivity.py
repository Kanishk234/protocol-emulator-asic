"""New extracted decode-cone sizing study; fixed-SPEF diagnostic only."""
from pathlib import Path
import extracted_sizing_sensitivity as base

SOURCE_RUN=38358706808
SOURCE_SHA='8e77722239af612fad2f590c322cab84600f76d0'
NETLIST_SHA='2128657d6bb519288b95d78ddca80e1b902412e8a9138897fa28a8da632a0345'
TARGETS={
    '_30044_':('sg13cmos5l_a21oi_1','sg13cmos5l_a21oi_2'),
    '_43917_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2'),
    '_43915_':('sg13cmos5l_and3_1','sg13cmos5l_and3_2')}
CASES={'baseline':{},'a21oi':{'_30044_':'sg13cmos5l_a21oi_2'},
       'nor2':{'_43917_':'sg13cmos5l_nor2_2'},
       'two_gates':{'_30044_':'sg13cmos5l_a21oi_2','_43917_':'sg13cmos5l_nor2_2'},
       'three_gates':{n:new for n,(old,new) in TARGETS.items()}}


def install_cases():
    base.SOURCE_RUN=SOURCE_RUN;base.SOURCE_SHA=SOURCE_SHA
    base.SOURCE_WORKFLOW='.github/workflows/gds-postant-route.yaml'
    base.SOURCE_DRT_ROOT=Path('runs/postant-route/drt')
    base.NETLIST_SHA=NETLIST_SHA;base.TARGETS=TARGETS;base.CASES=CASES
    base.EXTRA_VARIANTS={}

if __name__=='__main__':
    install_cases();base.main(Path('runs/postant-setup-sensitivity'))
