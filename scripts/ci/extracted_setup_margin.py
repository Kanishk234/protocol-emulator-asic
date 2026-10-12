"""Fixed-SPEF check of the remaining setup branch; no physical signoff."""
from pathlib import Path
import extracted_sizing_sensitivity as base
from extracted_setup_frontier import TARGETS, CURRENT

BEST=dict(CURRENT,_29918_='sg13cmos5l_nor3_2')
CASES={
    'baseline':{},
    'current_best':BEST,
    'short_first_delay':dict(BEST,hold12828='sg13cmos5l_dlygate4sd1_1'),
    'first_inv2':dict(BEST,_24812_='sg13cmos5l_inv_2'),
    'short_first_inv2':dict(BEST,hold12828='sg13cmos5l_dlygate4sd1_1',_24812_='sg13cmos5l_inv_2'),
}


def install_cases():
    base.TARGETS=TARGETS;base.CASES=CASES
    base.EXTRA_VARIANTS={'hold12828':{'sg13cmos5l_dlygate4sd1_1'}}


if __name__=='__main__':
    install_cases()
    base.main(Path('runs/extracted-setup-margin'))
