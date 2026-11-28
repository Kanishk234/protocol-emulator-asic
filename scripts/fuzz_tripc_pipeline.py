#!/usr/bin/env python3
"""Cross-check a bounded acyclic subset of tripc programs in tripsim."""
import argparse
from collections import Counter
import random

import tripc
import tripwire_spec as spec
from tripc.reaction import analyze_lane
from tripsim import Chip


def program(index, rng):
    first = rng.randrange(2)
    second = 1 - first
    output = rng.randrange(2)
    tags = rng.sample(list(spec.TAGS), rng.randint(1, len(spec.TAGS)))
    lane_tags = {first: tags, second: list(reversed(tags))}
    key1, key2 = (rng.getrandbits(16) for _ in range(2))
    additions = ''.join(f'    slot urgent: when I0 is {tag} do ADD O1 <- I0, K0, deq, keep\n'
                        for tag in lane_tags[first])
    xors = ''.join(f'    slot urgent: when I0 is {tag} do XOR O{output} <- I0, K0, deq, keep\n'
                   for tag in lane_tags[second])
    source = f"""program pipeline_{index}
connect L{first}.I0 <- HOST_IN
connect L{second}.I0 <- L{first}.O1
connect HOST_OUT <- L{second}.O{output}
lane L{first}:
    K0 = {key1}
{additions}lane L{second}:
    K0 = {key2}
{xors}"""
    data = [(spec.TAGS[rng.choice(tags)], rng.getrandbits(16)) for _ in range(rng.randint(1, 5))]
    expected = [(tag, ((word + key1) & 0xffff) ^ key2) for tag, word in data]
    counts = Counter(tag for tag, _ in data)
    expected_fires = [[counts[spec.TAGS[tag]] for tag in lane_tags[lane]] for lane in range(2)]
    return source, data, expected, expected_fires


def check(index, rng):
    source, data, expected, expected_fires = program(index, rng)
    image, _ = tripc.compile_text(source)
    for lane in image['lanes'].values():
        guarantees = analyze_lane([int(word, 16) for word in lane['slots']])
        if len(guarantees) != len(expected_fires[0]) or not all(
            result['selected_if_ready'] for result in guarantees
        ):
            raise AssertionError(f'{index}: unexpected compiler selection result')

    for period in (1, 2):
        chip = Chip(fire_period=period)
        tripc.load(chip, image)
        for tag, word in data:
            chip.host_push(word, tag)
        # Fixed observation window for these two hops and the serviced host.
        for _ in range(12 * len(data) + 4):
            due = []
            if chip.cycle % period == 0:
                for lane in chip.lanes:
                    if lane.running:
                        for slot, reflex in enumerate(lane.slots[:len(expected_fires[0])]):
                            if lane._ready(reflex):
                                due.append((lane, slot, lane.stats['fired'][slot]))
            clock = chip.cycle
            chip.step()
            for lane, slot, before in due:
                if lane.stats['fired'][slot] != before + 1:
                    raise AssertionError(f'{index}, fire_period={period}, clock={clock}: '
                                         f'eligible urgent slot missed EVAL\n{source}')
        observed = list(chip.host_out)
        fired = [lane.stats['fired'][:len(expected_fires[i])] for i, lane in enumerate(chip.lanes)]
        if observed != expected or fired != expected_fires:
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
