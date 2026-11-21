#!/usr/bin/env python3
"""Cross-check a bounded acyclic subset of tripc programs in tripsim."""
import argparse
import random

import tripc
import tripwire_spec as spec
from tripc.reaction import analyze_lane
from tripsim import Chip


def program(index, rng):
    first = rng.randrange(2)
    second = 1 - first
    output = rng.randrange(2)
    tag = rng.choice(tuple(spec.TAGS))
    key1, key2 = (rng.getrandbits(16) for _ in range(2))
    source = f"""program pipeline_{index}
connect L{first}.I0 <- HOST_IN
connect L{second}.I0 <- L{first}.O1
connect HOST_OUT <- L{second}.O{output}
lane L{first}:
    K0 = {key1}
    slot urgent: when I0 is {tag} do ADD O1 <- I0, K0, deq, keep
lane L{second}:
    K0 = {key2}
    slot urgent: when I0 is {tag} do XOR O{output} <- I0, K0, deq, keep
"""
    data = [rng.getrandbits(16) for _ in range(rng.randint(1, 5))]
    expected = [(spec.TAGS[tag], ((word + key1) & 0xffff) ^ key2) for word in data]
    return source, data, expected, spec.TAGS[tag]


def check(index, rng):
    source, data, expected, tag = program(index, rng)
    image, _ = tripc.compile_text(source)
    for lane in image['lanes'].values():
        guarantees = analyze_lane([int(word, 16) for word in lane['slots']])
        if len(guarantees) != 1 or not guarantees[0]['selected_if_ready']:
            raise AssertionError(f'{index}: unexpected compiler selection result')

    for period in (1, 2):
        chip = Chip(fire_period=period)
        tripc.load(chip, image)
        for word in data:
            chip.host_push(word, tag)
        # Fixed observation window for these two hops and the serviced host.
        chip.run_for(12 * len(data) + 4)
        observed = list(chip.host_out)
        fired = [lane.stats['fired'][0] for lane in chip.lanes]
        if observed != expected or fired != [len(data), len(data)]:
            raise AssertionError(
                f'{index}, fire_period={period}: {observed=} {expected=} {fired=}\n{source}')
    return len(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--programs', type=int, default=10_000)
    parser.add_argument('--seed', type=lambda value: int(value, 0), default=0x7A17)
    args = parser.parse_args()
    if args.programs <= 0:
        parser.error('--programs must be positive')
    rng = random.Random(args.seed)
    tokens = sum(check(index, rng) for index in range(args.programs))
    print(f'{args.programs} compiled pipelines, {tokens} tokens per cadence, '
          f'fire periods 1 and 2, seed {args.seed:#x}: PASS')


if __name__ == '__main__':
    main()
