"""Conservative host-channel service planner; no hardware rate certification.

Model: one direction, initially empty queue, arrival envelope burst + rate*t;
maximum initial service blackout followed by one-byte service at fixed bounded
intervals. Repeated pauses must already be included in that service guarantee.
"""
import argparse
from fractions import Fraction
import json
import math


def _number(value, name, positive=False):
    if isinstance(value, bool):
        raise ValueError(name + ' must be a finite number')
    try:
        number = Fraction(str(value))
    except (ValueError, ZeroDivisionError):
        raise ValueError(name + ' must be a finite number') from None
    if number < 0 or (positive and number == 0):
        raise ValueError(name + ' must be ' + ('positive' if positive else 'nonnegative'))
    return number


def plan(clock_hz, sck_hz, arrival_bytes_s, direction='read', blackout_us=0,
         overhead_us=0, burst_bytes=1, queue_bytes=2):
    clock = _number(clock_hz, 'clock_hz', True)
    sck = _number(sck_hz, 'sck_hz', True)
    arrival = _number(arrival_bytes_s, 'arrival_bytes_s')
    blackout = _number(blackout_us, 'blackout_us') / 1000000
    overhead = _number(overhead_us, 'overhead_us') / 1000000
    for value, name in ((burst_bytes, 'burst_bytes'), (queue_bytes, 'queue_bytes')):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(name + ' must be a nonnegative integer')
    if direction not in ('read', 'write'):
        raise ValueError('direction must be read or write')
    if sck > clock / 8:
        raise ValueError('SCK exceeds architecture clock/8 limit')
    # Current Warp API polls STATUS with a one-byte READ_ID transaction,
    # then transfers CH_READ (two bytes) or CH_WRITE (three bytes).
    # Conservative existing bit-bang framing: CS setup8, trailing-low4,
    # CS-high idle4 clocks per transaction. No new burst opcode assumed.
    wire_bytes = 3 if direction == 'read' else 4
    interval = Fraction(8 * wire_bytes, 1) / sck + Fraction(32, 1) / clock + 2 * overhead
    service = 1 / interval
    stable = arrival < service
    required = burst_bytes + math.ceil(arrival * (blackout + interval))
    return {'direction': direction, 'wire_bytes_per_payload_byte': wire_bytes,
            'transactions_per_payload_byte': 2,
            'service_interval_us': float(interval * 1000000),
            'service_capacity_bytes_s': float(service),
            'arrival_bytes_s': float(arrival), 'utilization': float(arrival * interval),
            'strict_service_margin': stable,
            'queue_bytes': queue_bytes, 'required_queue_bytes': required,
            'queue_sufficient_under_model': stable and queue_bytes >= required,
            'maximum_initial_blackout_us': float(blackout * 1000000),
            'scope': 'Analytical single-direction arrival/service model, not measured chip or board performance',
            'assumptions': ['Initially empty queue; burst + rate*t bounds arrivals',
                            'One initial blackout, then bounded service intervals including all host scheduling',
                            'One STATUS poll succeeds per payload; protocol-side consumption/production permits service',
                            'Other channel traffic and additional polls must be included in service overhead',
                            'Project clock and SPI levels meet architecture limits; timing signoff separate']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clock-hz', type=int, required=True)
    parser.add_argument('--sck-hz', type=int, required=True)
    parser.add_argument('--arrival-bytes-s', required=True)
    parser.add_argument('--direction', choices=('read', 'write'), default='read')
    parser.add_argument('--blackout-us', default='0')
    parser.add_argument('--overhead-us', default='0', help='Worst-case extra time per transaction, including scheduling')
    parser.add_argument('--burst-bytes', type=int, default=1)
    parser.add_argument('--queue-bytes', type=int, default=2)
    args = parser.parse_args()
    try:
        result = plan(**vars(args))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
