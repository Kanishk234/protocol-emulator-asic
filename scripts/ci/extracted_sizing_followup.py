"""Fixed-SPEF diagnostic of shared hold-delay cost, not a physical repair."""
from pathlib import Path
import extracted_sizing_sensitivity as base

# Same fixed extracted source, unchanged logic/connectivity. Delay variants are
# noninverting A/X cells in the exact pinned LEF; new hold failures are retained.
TARGETS={**base.TARGETS,
         'hold12828':('sg13cmos5l_dlygate4sd3_1','sg13cmos5l_dlygate4sd2_1'),
         '_24812_':('sg13cmos5l_inv_1','sg13cmos5l_inv_2')}
SMALL={n:new for n,(old,new) in base.TARGETS.items()}
CASES={
    'baseline':{},
    'small4':SMALL,
    'short_delay2':dict(SMALL,hold12828='sg13cmos5l_dlygate4sd2_1'),
    'short_delay1':dict(SMALL,hold12828='sg13cmos5l_dlygate4sd1_1'),
    'short_delay1_inv2':dict(SMALL,hold12828='sg13cmos5l_dlygate4sd1_1',_24812_='sg13cmos5l_inv_2'),
    'inv2_only':dict(SMALL,_24812_='sg13cmos5l_inv_2'),
}


def install_cases():
    base.TARGETS=TARGETS
    base.CASES=CASES
    # Permit the second reviewed delay variant explicitly; no arbitrary cell.
    base.EXTRA_VARIANTS={'hold12828':{'sg13cmos5l_dlygate4sd1_1'}}


if __name__=='__main__':
    install_cases()
    base.main(Path('runs/extracted-sizing-followup'))
