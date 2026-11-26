"""Exact occupancy analysis for one blocking channel with periodic service."""
from math import lcm

from .channel_graph import forwarding_ports


def _validate_schedule(period, phase):
    if (type(period) is not int or period <= 0
            or type(phase) is not int or not 0 <= phase < period):
        raise ValueError('Periods must be positive integers and phases within the period')


def analyze_periodic_channel(arrival_period, service_period, *,
                             arrival_phase=0, service_phase=0, max_cycle=100_000):
    """Analyze an initially empty, one-token channel under fixed schedules.

    Each arrival requests a load. A service opportunity takes the current
    token if present. A token taken at the current edge releases the producer
    for the next clock, so a simultaneous new arrival can still overrun.
    Phase offsets select the first event, relative to clock zero.
    """
    for period, phase in ((arrival_period, arrival_phase), (service_period, service_phase)):
        _validate_schedule(period, phase)
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


def analyze_periodic_pipeline(arrival_period, service_period, *,
                              arrival_phase=0, service_phase=0, fire_period=1, max_cycle=100_000):
    """Check two empty blocking channels joined by one unconditional reflex.

    The reflex consumes at EVAL, reserves its output, and loads it at EXEC
    one clock later. Both receivers can see only already-committed tokens.
    """
    _validate_schedule(arrival_period, arrival_phase)
    _validate_schedule(service_period, service_phase)
    _validate_schedule(fire_period, 0)
    if type(max_cycle) is not int or max_cycle <= 0:
        raise ValueError('Simulation limit must be a positive integer')

    repeat = lcm(arrival_period, service_period, fire_period)
    incoming = outgoing = reserved = False
    seen = set()
    for clock in range(max_cycle + 1):
        if clock % repeat == 0:
            state = incoming, outgoing, reserved
            if state in seen:
                return {'status': 'no_overrun', 'clocks_checked': clock}
            seen.add(state)
        if clock == max_cycle:
            break
        arrives = clock % arrival_period == arrival_phase
        if arrives and incoming:
            return {'status': 'overrun', 'clock': clock}
        serves = clock % service_period == service_phase
        evaluates = clock % fire_period == 0 and incoming and not (outgoing or reserved)
        incoming = arrives or (incoming and not evaluates)
        outgoing = reserved or (outgoing and not serves)
        reserved = evaluates
    return {'status': 'unknown', 'clocks_checked': max_cycle}


def analyze_compiled_channel(image, schedule):
    """Check a declared schedule on a compiled, unfiltered point-to-point binding."""
    required = {'consumer', 'arrival_period', 'service_period'}
    optional = {'arrival_phase', 'service_phase'}
    if not isinstance(schedule, dict) or not required <= schedule.keys() <= required | optional:
        raise ValueError('Expected consumer, arrival_period, service_period and optional phases')
    consumer = schedule['consumer']
    producer = _blocking_producer(image, consumer)
    args = {key: value for key, value in schedule.items() if key != 'consumer'}
    return {'producer': producer, 'consumer': consumer, **analyze_periodic_channel(**args)}


def _blocking_producer(image, consumer):
    bindings = {port: (producer, mode, accept) for port, producer, mode, accept in image['connect']}
    if not isinstance(consumer, str) or consumer not in bindings:
        raise ValueError('Expected a configured consumer port')
    producer, mode, accept = bindings[consumer]
    if mode != 'blocking' or accept != 0xf:
        raise ValueError('Expected an unfiltered blocking consumer')
    if any(port != consumer and bound_producer == producer and bound_mode == 'blocking'
           for port, (bound_producer, bound_mode, _) in bindings.items()):
        raise ValueError('Producer has more than one blocking consumer')
    return producer


def analyze_compiled_pipeline(image, schedule):
    """Check a declared schedule on a host-to-host, single-reflex pipeline."""
    required = {'lane', 'arrival_period', 'service_period'}
    optional = {'arrival_phase', 'service_phase', 'fire_period'}
    if not isinstance(schedule, dict) or not required <= schedule.keys() <= required | optional:
        raise ValueError('Expected lane, arrival_period, service_period and optional phases or fire_period')
    lane = schedule['lane']
    if not isinstance(lane, str) or set(image['lanes']) != {lane}:
        raise ValueError('Expected exactly one programmed forwarding lane')
    ports = forwarding_ports(image['lanes'][lane]['slots'])
    if ports is None:
        raise ValueError('Expected one unconditional forwarding slot')
    input_port, output_port = f'{lane}.I{ports[0]}', f'{lane}.O{ports[1]}'
    if _blocking_producer(image, input_port) != 'HOST_IN' or _blocking_producer(image, 'HOST_OUT') != output_port:
        raise ValueError('Expected a blocking HOST_IN to lane to HOST_OUT pipeline')
    args = {key: value for key, value in schedule.items() if key != 'lane'}
    return {'lane': lane, 'input': input_port, 'output': output_port,
            **analyze_periodic_pipeline(**args)}
