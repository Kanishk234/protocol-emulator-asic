"""Summarize pinned-tool introspection; not a routing-preservation qualification."""
import argparse
import json
from pathlib import Path
import re


def summarize(text):
    pairs=re.findall(r'^TRIPWIRE CAPABILITY (\w+) ([01])\s*$',text,re.M)
    expected={'global_route','read_guides','read_global_route_segments','write_global_route_segments','probe_complete'}
    if len(pairs)!=len(expected) or {k for k,v in pairs}!=expected:
        raise ValueError('Missing or duplicate capability evidence')
    capabilities={k:v=='1' for k,v in pairs}
    if not capabilities.pop('probe_complete'): raise ValueError('Probe did not complete')
    help_text=re.search(r'^TRIPWIRE HELP BEGIN global_route\s*$(.*?)^TRIPWIRE HELP END global_route\s*$',text,re.M|re.S)
    incremental=bool(capabilities['global_route'] and help_text and '-start_incremental' in help_text[1] and '-end_incremental' in help_text[1])
    return dict(command_capabilities=capabilities,incremental_flags_documented=incremental,
        checkpoint_restoration_tested=False,unchanged_routes_preserved=False,
        physical_change_applied=False,official_signoff=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path);parser.add_argument('output',type=Path)
    a=parser.parse_args();result=summarize(a.log.read_text())
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
