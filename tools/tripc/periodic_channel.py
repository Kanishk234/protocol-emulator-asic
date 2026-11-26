"""Exact occupancy analysis for one blocking channel with periodic service."""
from math import lcm


def analyze_periodic_channel(arrival_period, service_period, *,
                             arrival_phase=0, service_phase=0, max_cycle=100_000):
    """Analyze an initially empty, one-token channel under fixed schedules.

    Each arrival requests a load. A service opportunity takes the current
    token if present. A token taken at the current edge releases the producer
    for the next clock, so a simultaneous new arrival can still overrun.
    Phase offsets select the first event, relative to clock zero.
    """
    for period, phase in ((arrival_period, arrival_phase), (service_period, service_phase)):
        if (type(period) is not int or period <= 0
                or type(phase) is not int or not 0 <= phase < period):
            raise ValueError('Periods must be positive integers and phases within the period')
    if type(max_cycle) is not int or max_cycle <= 0:
        raise ValueError('Simulation limit must be a positive integer')

    repeat = lcm(arrival_period, service_period)
    occupied = False
    seen = set()
    for clock in range(max_cycle):
        phase = clock % repeat
        if phase == 0:
            if occupied in seen:
                return {'status': 'no_overrun', 'clocks_checked': clock}
            seen.add(occupied)
        arrives = clock % arrival_period == arrival_phase
        serves = clock % service_period == service_phase
        if arrives and occupied:
            return {'status': 'overrun', 'clock': clock}
        occupied = arrives or (occupied and not serves)
    if max_cycle % repeat == 0 and occupied in seen:
        return {'status': 'no_overrun', 'clocks_checked': max_cycle}
    return {'status': 'unknown', 'clocks_checked': max_cycle}


def analyze_compiled_channel(image, schedule):
    """Check a declared schedule on a compiled, unfiltered point-to-point binding."""
    required = {'consumer', 'arrival_period', 'service_period'}
    optional = {'arrival_phase', 'service_phase'}
    if not isinstance(schedule, dict) or not required <= schedule.keys() <= required | optional:
        raise ValueError('Expected consumer, arrival_period, service_period and optional phases')
    consumer = schedule['consumer']
    bindings = {port: (producer, mode, accept) for port, producer, mode, accept in image['connect']}
    if not isinstance(consumer, str) or consumer not in bindings:
        raise ValueError('Expected a configured consumer port')
    producer, mode, accept = bindings[consumer]
    if mode != 'blocking' or accept != 0xf:
        raise ValueError('Expected an unfiltered blocking consumer')
    if any(port != consumer and bound_producer == producer and bound_mode == 'blocking'
           for port, (bound_producer, bound_mode, _) in bindings.items()):
        raise ValueError('Producer has more than one blocking consumer')
    args = {key: value for key, value in schedule.items() if key != 'consumer'}
    return {'producer': producer, 'consumer': consumer, **analyze_periodic_channel(**args)}
