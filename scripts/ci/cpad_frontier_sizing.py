"""Bounded cumulative gate sizing on five failing path families; fixed RC only."""
import cpad_sizing_probe as probe

TARGETS = {'_24522_': ('sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2'),
 '_30153_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_37356_': ('sg13cmos5l_a21oi_1', 'sg13cmos5l_a21oi_2'),
 '_24743_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_30649_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_30523_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_30495_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_30156_': ('sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2'),
 '_30618_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_24507_': ('sg13cmos5l_nand2_1', 'sg13cmos5l_nand2_2'),
 '_30589_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2'),
 '_30689_': ('sg13cmos5l_nor3_1', 'sg13cmos5l_nor3_2')}


def main():
    probe.TARGETS = TARGETS
    ordered = list(TARGETS)
    probe.CASES = {'baseline': {}, **{
        f'top{count}': {name: TARGETS[name][1] for name in ordered[:count]}
        for count in (2, 4, 8, 12)}}
    probe.main()


if __name__ == '__main__':
    main()
