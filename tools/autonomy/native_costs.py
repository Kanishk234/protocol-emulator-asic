"""Read-only cost/residual fingerprint; never accept hypothetical accounting.

Compares raw minus live-layer-weighted STEP MULTISETS with the hypothesis
sum(soft-net multiplicity * (scalar cost - live layer demand)). A match is a
diagnostic fingerprint, not a replacement ledger, native authentication or fix.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from autonomy import native_corridor


def _edge(edge):
    return dict(zip(('direction', 'layer', 'x', 'y'), edge))


def diagnose_bytes(raw):
    snapshot = native_corridor.parse_bytes(raw)
    groups, weighted, hypothetical = Counter(), Counter(), Counter()
    divergent_soft = []
    for slot, net in sorted(snapshot.nets.items()):
        groups[net['soft_ndr'], net['clock'], net['scalar_cost'], tuple(net['demands'])] += 1
        if net['soft_ndr'] and net['scalar_cost'] != 1:
            divergent_soft.append({'slot': slot, 'database_id': net['db_id'], 'name': net['name'],
                'clock': net['clock'], 'scalar_cost': net['scalar_cost'], 'layer_demands': net['demands']})
        for edge, count in net['planar_step_multiplicity'].items():
            demand = net['demands'][edge[1]]
            weighted[edge] += count*demand
            if net['soft_ndr']:
                hypothetical[edge] += count*(net['scalar_cost']-demand)
    residual = {edge: data[1]-weighted[edge] for edge, data in snapshot.edges.items()}
    residual_support = {edge for edge,value in residual.items() if value}
    hypothesis_support = {edge for edge in snapshot.edges if hypothetical[edge]}
    support = residual_support | hypothesis_support
    overlap = residual_support & hypothesis_support
    signs_match = lambda edge: (residual[edge] > 0) == (hypothetical[edge] > 0)
    rows=[]
    for edge in sorted(support):
        observed, predicted = residual[edge], hypothetical[edge]
        rows.append({'edge': _edge(edge), 'raw_usage': snapshot.edges[edge][1],
                     'layer_multiset_usage': weighted[edge], 'raw_minus_layer_multiset': observed,
                     'hypothetical_soft_scalar_minus_layer': predicted,
                     'residual_minus_hypothesis': observed-predicted})
    signed_summary = lambda values: {'signed_sum': sum(values), 'l1_sum': sum(abs(v) for v in values),
        'positive_edges': sum(v > 0 for v in values), 'negative_edges': sum(v < 0 for v in values)}
    residual_values=list(residual.values())
    hypothesis_values=[hypothetical[edge] for edge in snapshot.edges]
    mismatch = {edge for edge in support if residual[edge] != hypothetical[edge]}
    return {
        'schema_version': 1, 'input_sha256': snapshot.sha256,
        'conclusion_scope': 'native_cost_residual_fingerprint_only',
        'native_inputs_authenticated': False, 'physical_acceptance': False, 'timing_acceptance': False,
        'hypothetical_weighting_accepted': False,
        'authoritative_accounting': 'live_layer_demand_times_STEP_multiset',
        'original_usage_ledger_reconciled': not residual_support,
        'raw_edge_count': len(snapshot.edges), 'live_net_count': len(snapshot.nets),
        'cost_distribution': [{'soft_ndr': soft, 'clock': clock, 'scalar_cost': scalar,
                               'layer_demands': list(demands), 'net_count': count}
                              for (soft,clock,scalar,demands),count in sorted(groups.items())],
        'soft_scalar_not_one': divergent_soft,
        'comparison': {
            'all_edge_exact_match': not mismatch,
            'all_edge_exact_match_edges': len(snapshot.edges)-len(mismatch),
            'support_exact_match': residual_support == hypothesis_support,
            'residual_support_edges': len(residual_support), 'hypothesis_support_edges': len(hypothesis_support),
            'overlapping_support_edges': len(overlap),
            'off_hypothesis_support_edges': len(residual_support-hypothesis_support),
            'hypothesis_only_support_edges': len(hypothesis_support-residual_support),
            'signed_magnitude_mismatch_edges': len(mismatch),
            'overlap_equal_signed_magnitude_edges': sum(residual[e] == hypothetical[e] for e in overlap),
            'overlap_same_sign_edges': sum(signs_match(edge) for edge in overlap),
            'overlap_opposite_sign_edges': sum(not signs_match(edge) for edge in overlap),
            'overlap_equal_absolute_magnitude_edges': sum(abs(residual[e]) == abs(hypothetical[e]) for e in overlap),
            'residual_minus_hypothesis_l1': sum(abs(residual[e]-hypothetical[e]) for e in support),
            'residual': signed_summary(residual_values), 'hypothesis': signed_summary(hypothesis_values),
        },
        'edge_comparison_scope': 'Every edge with nonzero residual or nonzero aggregate hypothesis; omitted edges have both exactly zero',
        'edge_comparisons': rows,
    }


def diagnose_file(path):
    with Path(path).open('rb') as stream:
        return diagnose_bytes(stream.read(native_corridor.MAX_BYTES+1))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=diagnose_file(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
