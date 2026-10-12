"""Unchanged cell placement and unaffected route audit for bounded edits."""
import re
from route_segment_audit import compare


def placements(layout):
    section=layout.split('COMPONENTS ',1)[1].split('END COMPONENTS',1)[0]
    result={}
    for name,master,body in re.findall(r'^\s*- (\S+) (\S+)(.*?);',section,re.M|re.S):
        hit=re.search(r'\+ (?:PLACED|FIXED) \(\s*(-?\d+)\s+(-?\d+)\s*\) (\S+)',body)
        if not hit or name in result: raise ValueError('Missing or duplicate placed component')
        result[name]=(master,int(hit[1]),int(hit[2]),hit[3])
    if not result:raise ValueError('Missing component placements')
    return result


def audit(before_def,after_def,before_segments,after_segments,proposal,antenna_nets=()):
    old,new=placements(before_def),placements(after_def)
    if any(new.get(n)!=p for n,p in old.items()):
        raise ValueError('Incremental repair moves or changes an existing component')
    allowed={g['source_net'] for g in proposal['groups']}|{g['net'] for g in proposal['groups']}|set(antenna_nets)
    result=compare(before_segments,after_segments,allowed)
    if not result['unchanged_routes_preserved']:raise ValueError('Unexpected route changes outside planned nets')
    return result


def added_antenna_nets(before_nl,after_nl):
    from event_nor2_screen import logical_cells,validate_antenna_only_changes
    validate_antenna_only_changes(before_nl,after_nl)
    old,new=logical_cells(before_nl),logical_cells(after_nl)
    return sorted({v.strip().removeprefix('\\') for n,(m,pins) in new.items() if n not in old
                   for p,v in pins if p not in ('VDD','VSS')})


def require_live_demand(log):
    reports=log.split('Final congestion report:')[1:]
    if len(reports)<2:raise ValueError('Missing initial/final live congestion evidence')
    for report in (reports[0],reports[-1]):
        match=re.search(r'^\s*Total\s+\d+\s+(\d+)\s+',report,re.M)
        if not match or int(match[1])<=0:raise ValueError('Routing demand was not initialized')
    return True


def reported_antenna_nets(report):
    """Pinned checker writes only violating nets without -verbose."""
    names=re.findall(r'^Net: (\S+)\s*$',report,re.M)
    if (not names and report.strip()) or len(names)!=len(set(names)):
        raise ValueError('Missing or duplicate pre-repair antenna violations')
    return sorted(names)
