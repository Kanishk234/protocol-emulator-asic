#!/usr/bin/env python3
"""Cross-check declared schedules on randomized compiled forwarding chains."""
import argparse
from collections import Counter
from math import lcm
import random

import tripc
from tripc.periodic_channel import analyze_compiled_pipeline
from tripsim import Chip


def program(index, rng):
    lanes = rng.sample(['L0', 'L1'], rng.randint(1, 2))
    producers = ['HOST_IN']
    slots = []
    for lane in lanes:
        # A lane's O0 can reach its peer through I1; O1 can use either input.
        pin = 1 if producers[-1].endswith('.O0') else rng.randrange(2)
        port = rng.randrange(2)
        key = rng.getrandbits(16)
        slots.append(
            f'connect {lane}.I{pin} <- {producers[-1]}\n'
            f'lane {lane}:\n'
            f'    K0 = {key}\n'
            f'    slot urgent: do ADD O{port} <- I{pin}, K0, deq\n'
        )
        producers.append(f'{lane}.O{port}')
    source = f'program schedule_{index}\n' + ''.join(slots) + f'connect HOST_OUT <- {producers[-1]}\n'
    arrivals, service = rng.randint(1, 9), rng.randint(1, 9)
    return source, {
        'lanes': lanes,
        'arrival_period': arrivals,
        'arrival_phase': rng.randrange(arrivals),
        'service_period': service,
        'service_phase': rng.randrange(service),
        'fire_period': rng.randint(1, 2),
    }


def check(index, rng):
    source, schedule = program(index, rng)
    image, _ = tripc.compile_text(source)
    result = analyze_compiled_pipeline(image, schedule)
    status = result['status']
    if status not in ('no_overrun', 'overrun'):
        raise AssertionError(f'{index}: unexpected result for {schedule}: {result}')
    arrivals, service, cadence = (schedule[key] for key in ('arrival_period', 'service_period', 'fire_period'))
    # For a claimed safe case, observe another complete combined phase period.
    stop = (result['clocks_checked'] + lcm(arrivals, service, cadence)
            if status == 'no_overrun' else result['clock'] + 1)
    chip = Chip(fire_period=cadence)
    tripc.load(chip, image)
    producer = chip.fabric.producers['HOST_IN']
    first_overrun = None
    for clock in range(stop):
        if clock % arrivals == schedule['arrival_phase']:
            if not producer.free():
                first_overrun = clock
                break
            producer.load(0, clock)
        chip.host_fifo_depth = int(clock % service == schedule['service_phase'])
        chip.step()
        chip.host_out.clear()
    if first_overrun != result.get('clock'):
        raise AssertionError(f'{index}: model overrun {first_overrun}, checker {result}\n{schedule}\n{source}')
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--programs', type=int, default=10_000)
    parser.add_argument('--seed', type=lambda value: int(value, 0), default=0x21F0)
    args = parser.parse_args()
    if args.programs <= 0:
        parser.error('--programs must be positive')
    rng = random.Random(args.seed)
    counts = Counter(check(index, rng) for index in range(args.programs))
    print(f'{args.programs} compiled programs, seed {args.seed:#x}: '
          f'{counts["no_overrun"]} safe, {counts["overrun"]} overruns, no contradictions')


if __name__ == '__main__':
    main()
