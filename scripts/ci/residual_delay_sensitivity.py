"""Measured improved-source shared delay tradeoff; diagnostic only."""
from pathlib import Path
import residual_setup_sensitivity as source
import extracted_sizing_sensitivity as base

TARGETS={**source.TARGETS,
    'hold12766':('sg13cmos5l_dlygate4sd3_1','sg13cmos5l_dlygate4sd2_1'),
    'hold12715':('sg13cmos5l_dlygate4sd3_1','sg13cmos5l_dlygate4sd2_1')}
BEST={'_43582_':'sg13cmos5l_nor2_2'}
CASES={'baseline':{},'nor2':BEST,
       'medium12766':dict(BEST,hold12766='sg13cmos5l_dlygate4sd2_1'),
       'medium12715':dict(BEST,hold12715='sg13cmos5l_dlygate4sd2_1'),
       'both_medium':dict(BEST,hold12766='sg13cmos5l_dlygate4sd2_1',hold12715='sg13cmos5l_dlygate4sd2_1'),
       'full_medium':dict(source.CASES['combined'],hold12766='sg13cmos5l_dlygate4sd2_1',hold12715='sg13cmos5l_dlygate4sd2_1')}


if __name__=='__main__':
    source.install_cases();base.TARGETS=TARGETS;base.CASES=CASES
    base.main(Path('runs/residual-delay-sensitivity'))
