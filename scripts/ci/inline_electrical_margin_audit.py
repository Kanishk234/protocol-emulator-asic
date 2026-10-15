"""Independently prove each dynamic identity-buffer source had measured risk."""
from pathlib import Path
from electrical_margin_summary import summarize
from post_antenna_fanout_audit import audit as audit_history


def sources(root, iteration):
    corners = summarize(list(Path(root).glob(f'postant_margin_{iteration}_*.rpt')))
    return {name for data in corners.values() for name, rows in data['nets'].items()
            if any((rows.get(k, {}).get('utilization') or 0) > .45
                   for k in ('slew', 'capacitance'))}


def audit(before, after, root, log):
    result = audit_history(before, after, root, log, margin_audit=sources)
    remaining = sources(root, result['post_antenna_batches'])
    if remaining:
        raise ValueError('Inline electrical margin did not converge')
    result.update(inline_electrical_margin_audited=True, inline_electrical_margin_limit=.45)
    return result
