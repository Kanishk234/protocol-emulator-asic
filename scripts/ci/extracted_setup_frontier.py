"""Measure the next shared setup cone with fixed extracted RC; no routing."""
from pathlib import Path
import extracted_sizing_sensitivity as base
from extracted_sizing_followup import TARGETS as PREVIOUS_TARGETS, SMALL

TARGETS={**PREVIOUS_TARGETS,
    '_29918_':('sg13cmos5l_nor3_1','sg13cmos5l_nor3_2'),
    'hold12766':('sg13cmos5l_dlygate4sd3_1','sg13cmos5l_dlygate4sd2_1')}
CURRENT=dict(SMALL,hold12828='sg13cmos5l_dlygate4sd2_1')
CASES={
    'baseline':{},
    'current_best':CURRENT,
    'nor3_only':dict(CURRENT,_29918_='sg13cmos5l_nor3_2'),
    'delay2_only':dict(CURRENT,hold12766='sg13cmos5l_dlygate4sd2_1'),
    'delay2_nor3':dict(CURRENT,hold12766='sg13cmos5l_dlygate4sd2_1',_29918_='sg13cmos5l_nor3_2'),
    'delay1_nor3':dict(CURRENT,hold12766='sg13cmos5l_dlygate4sd1_1',_29918_='sg13cmos5l_nor3_2'),
}


def install_cases():
    base.TARGETS=TARGETS;base.CASES=CASES
    base.EXTRA_VARIANTS={'hold12766':{'sg13cmos5l_dlygate4sd1_1'}}


if __name__=='__main__':
    install_cases()
    base.main(Path('runs/extracted-setup-frontier'))
