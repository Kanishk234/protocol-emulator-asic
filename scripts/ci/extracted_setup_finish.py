"""Fixed-SPEF remaining NOR2/AND4 load study; never physical qualification."""
from pathlib import Path
import extracted_sizing_sensitivity as base
from extracted_setup_margin import TARGETS as PREVIOUS_TARGETS, CASES as PREVIOUS_CASES

TARGETS={**PREVIOUS_TARGETS,
    '_24896_':('sg13cmos5l_nor2_1','sg13cmos5l_nor2_2'),
    '_25926_':('sg13cmos5l_and4_1','sg13cmos5l_and4_2')}
BEST=PREVIOUS_CASES['short_first_inv2']
CASES={'baseline':{},'current_best':BEST,
       'nor2':dict(BEST,_24896_='sg13cmos5l_nor2_2'),
       'and4':dict(BEST,_25926_='sg13cmos5l_and4_2'),
       'both':dict(BEST,_24896_='sg13cmos5l_nor2_2',_25926_='sg13cmos5l_and4_2')}


def install_cases():
    base.TARGETS=TARGETS;base.CASES=CASES
    base.EXTRA_VARIANTS={'hold12828':{'sg13cmos5l_dlygate4sd1_1'}}


if __name__=='__main__':
    install_cases()
    base.main(Path('runs/extracted-setup-finish'))
