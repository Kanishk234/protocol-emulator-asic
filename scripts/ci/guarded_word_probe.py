"""Audit a tiny guarded-mask selector; never qualify the full TRIPWIRE design."""
import argparse
import json
from pathlib import Path
import re


PROTECTION_RX = r'(^|[./])trw_guard_mask[01]_(node|diode)$'


def logged_objects(text):
    """Normalize only Tcl's bracket escapes in actual native protection messages."""
    return {(kind, re.sub(r'\\([\[\]])', r'\1', name))
            for kind, name in re.findall(
                r"(?m)^\[INFO\] (Net|Instance) '([^'\n]+)' matched don't touch "
                r"regular expression, setting as don't touch", text)}


def connectivity(text, width=7, group=6):
    """Check the two-row probe's diode, driver and A22OI mask terminals."""
    cells = {}
    for master, name, body in re.findall(
            r'\b(sg13cmos5l_\w+)\s+(\S+)\s*\((.*?)\);', text, re.S):
        name = name.removeprefix('\\')
        if name in cells:
            raise ValueError('Duplicate mapped cell')
        cells[name] = (master, {pin: net.strip().removeprefix('\\') for pin, net in
                               re.findall(r'\.(\w+)\s*\(\s*([^)]*?)\s*\)', body)})
    sinks = {n: c for n, c in cells.items() if n.endswith('.trw_guard_sink')}
    failures = []
    nodes = set()
    diode_names = set()
    if len(sinks) != width:
        failures.append('Wrong guarded sink count')
    for name, (master, pins) in sinks.items():
        if master != 'sg13cmos5l_a22oi_1':
            failures.append('Wrong guarded gate function: ' + name)
        if '.g_bit[' not in name:
            failures.append('Missing group identity: ' + name)
            continue
        prefix = name.split('.g_bit[', 1)[0]
        for index, pin in [(0, 'A1'), (1, 'B1')]:
            stem = prefix + ('.g_second' if index else '')
            diode = cells.get(stem + f'.trw_guard_mask{index}_diode')
            driver = cells.get(stem + f'.mask{index}_driver')
            node = pins.get(pin)
            if (not node or not re.search(PROTECTION_RX, node)
                    or not node.endswith(f'trw_guard_mask{index}_node')
                    or diode is None or diode[0] != 'sg13cmos5l_antennanp'
                    or diode[1].get('A') != node
                    or driver is None
                    or not re.fullmatch(r'sg13cmos5l_buf_(?:2|4|8|16)', driver[0])
                    or driver[1].get('X') != node):
                failures.append('Mask diode/driver/gate connection lost: ' + name + '/' + pin)
            else:
                nodes.add(node)
                diode_names.add(stem + f'.trw_guard_mask{index}_diode')
    expected_nodes = 2 * ((width + group - 1) // group)
    if len(nodes) != expected_nodes:
        failures.append('Wrong protected mask-node count')
    return dict(connectivity_preserved=not failures, failures=failures,
                guarded_gate_count=len(sinks), protected_node_count=len(nodes),
                protected_objects=sorted(nodes | diode_names))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('physical', type=Path)
    parser.add_argument('--protected', choices=['true', 'false'], required=True)
    args = parser.parse_args()
    root = args.physical
    paths = list(root.glob('*-openroad-resizertimingpostgrt/*.nl.v'))
    if len(paths) != 1:
        raise ValueError('Missing unique final native netlist')
    result = connectivity(paths[0].read_text())
    protected = args.protected == 'true'
    config = json.loads((root / 'resolved.json').read_text())
    expected = PROTECTION_RX if protected else '$^'
    if config['RSZ_DONT_TOUCH_RX'] != expected:
        raise ValueError('Wrong native protection configuration')
    # Freezing a sink gate would also freeze its data inputs. Protect only mask
    # nodes/diodes so native repair remains free to buffer the data paths.
    for leaf in ['trw_guard_sink', 'mask0_driver', 'mask1_driver']:
        if re.search(PROTECTION_RX, 'u.' + leaf):
            raise ValueError('Protection freezes an upstream driver or data sink')
    logs = list(root.glob('*-openroad-*/openroad-*.log'))
    required = {('Net' if name.endswith('_node') else 'Instance', name)
                for name in result['protected_objects']}
    matched = [str(p.relative_to(root)) for p in logs
               if required and required <= logged_objects(p.read_text())]
    covered = all(any('-openroad-' + stage + '/' in path for path in matched)
                  for stage in ['repairdesignpostgpl', 'resizertimingpostcts',
                                'repairdesignpostgrt', 'resizertimingpostgrt'])
    metrics = list(root.glob('*-openroad-stamidpnr-3/or_metrics_out.json'))
    if len(metrics) != 1:
        raise ValueError('Missing fresh native timing metrics')
    raw = json.loads(metrics[0].read_text())
    if not any(k.startswith('timing__setup__ws__corner:') for k in raw):
        raise ValueError('Missing native setup measurement')
    result.update(protected=protected, native_protection_logs=matched,
                  all_repair_stages_exercised_protection=covered,
                  native_metrics={k: v for k, v in raw.items()
                                  if k.startswith(('timing__', 'design__max_'))},
                  full_design_qualification=False, detailed_routing_performed=False,
                  scope='Two-row selector mask connectivity only; data/reduction inputs unprotected')
    (root / 'guarded_word_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    if protected and not result['connectivity_preserved']:
        raise ValueError('Guarded mask connections were not preserved through native repair')
    if protected and not covered:
        raise ValueError('Missing complete native protection log evidence')


if __name__ == '__main__':
    main()
