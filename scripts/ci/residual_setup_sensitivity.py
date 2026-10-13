"""Fixed-SPEF residual setup candidates on the improved combined route."""
from pathlib import Path
import extracted_sizing_sensitivity as base

SOURCE_RUN=38336141213
SOURCE_SHA='a1642e654ceaae36ee082555e1144b728e3fcb22'
TARGETS={
    '_43582_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2'),
    'place7208':('sg13cmos5l_buf_1','sg13cmos5l_buf_4'),
    '_25727_':('sg13cmos5l_nor4_1','sg13cmos5l_nor4_2')}
CASES={'baseline':{},'nor2':{'_43582_':'sg13cmos5l_nor2_2'},
       'buf4':{'place7208':'sg13cmos5l_buf_4'},'nor4':{'_25727_':'sg13cmos5l_nor4_2'},
       'combined':{n:new for n,(old,new) in TARGETS.items()},
       'strong_buffer':dict(_43582_='sg13cmos5l_nor2_2',place7208='sg13cmos5l_buf_8',_25727_='sg13cmos5l_nor4_2')}


def install_cases():
    base.SOURCE_RUN=SOURCE_RUN;base.SOURCE_SHA=SOURCE_SHA
    base.SOURCE_WORKFLOW='.github/workflows/gds-combined-physical-route.yaml'
    base.SOURCE_DRT_ROOT=Path('runs/combined-physical-route/drt')
    base.NETLIST_SHA='08f99cf0d24fc7cc238ca80252d388500a0e845f4c6888dcbc71d4e7f5e00e1a'
    base.TARGETS=TARGETS;base.CASES=CASES
    base.EXTRA_VARIANTS={'place7208':{'sg13cmos5l_buf_8'}}


if __name__=='__main__':
    install_cases()
    base.main(Path('runs/residual-setup-sensitivity'))
