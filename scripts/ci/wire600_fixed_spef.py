"""Portable fixed-SPEF sensitivity; requires exact CI baseline reproduction.

This measures strength changes with old routes. It never qualifies new placement,
routes, antenna behavior or fanout. Real screening and clean replay remain needed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

from event_nor2_screen import logical_cells
from wire600_extracted_reserve import REVIEW

CORNERS = [('slow_1p08V_125C','slow_1p08V_125C'),
           ('typ_1p20V_25C','typ_1p20V_25C'),
           ('fast_1p32V_m40C','fast_1p32V_m55C')]


def changed_netlist(text, targets=None):
    old = logical_cells(text)
    result = text
    expected = dict(old)
    # The first two substitutions belong to the already executed preparation.
    targets = REVIEW['resizes'][2:] if targets is None else targets
    for target in targets:
        name, master, new = (target[k] for k in ('instance','old_master','new_master'))
        if old.get(name,(None,))[0] != master:
            raise ValueError('Wrong extracted strength source')
        normalized = {p:n.strip().removeprefix('\\') for p,n in old[name][1]}
        if normalized != target['pins']:
            raise ValueError('Wrong extracted strength pins')
        pattern = r'\b'+re.escape(master)+r'(\s+)'+re.escape(name)+r'(?=\s*\()'
        result, count = re.subn(pattern,lambda m:new+m[1]+name,result)
        if count != 1:
            raise ValueError('Ambiguous extracted strength substitution')
        expected[name] = (new,old[name][1])
    if logical_cells(result) != expected:
        raise ValueError('Strength experiment changed unrelated logic/connections')
    return result


def slack(report):
    values = re.findall(r'^\s*([-+\d.eE]+)\s+slack \((?:MET|VIOLATED)\)',report,re.M)
    if not values or any(not math.isfinite(float(v)) for v in values):
        raise ValueError('Missing finite fixed-SPEF slack')
    return min(map(float,values))


def diagnose(root, library_dir, macro_dir, sta, output, *, review=REVIEW):
    root, output = Path(root).resolve(), Path(output).resolve()
    for name, sha in review['diagnostic_binding'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != sha:
            raise ValueError('Wrong fixed-SPEF input: '+name)
    output.mkdir(exist_ok=False)
    prefix = root/'runs/extracted-timing'
    source = prefix/'08-openroad-fillinsertion/tt_um_tripwire.nl.v'
    text = source.read_text()
    reference = json.loads((prefix/'corner_summary.json').read_text())
    results = {}
    targets = review.get('diagnostic_resizes', review['resizes'][2:])
    selected = 'strength'+str(len(targets))
    for case, nl in [('baseline',text),(selected,changed_netlist(text, targets))]:
        netlist = output/(case+'.v'); netlist.write_text(nl)
        results[case] = {}
        for corner, macro_corner in CORNERS:
            tag = case+'-'+corner
            lib = (Path(library_dir)/('sg13cmos5l_stdcell_'+corner+'.lib')).resolve()
            macro = (Path(macro_dir)/('RM_IHPSG13_1P_512x16_c2_bm_bist_'+macro_corner+'.lib')).resolve()
            tcl = f'''read_liberty {{{lib}}}
read_liberty {{{macro}}}
read_verilog {{{netlist}}}
link_design tt_um_tripwire
read_sdc {{{prefix/'final/sdc/tt_um_tripwire.sdc'}}}
read_spef {{{prefix/'10-openroad-rcx/nom/tt_um_tripwire.nom.spef'}}}
report_checks -path_delay max -group_count 1 -digits 6 > {{{output/(tag+'.max.rpt')}}}
report_checks -path_delay min -group_count 1 -digits 6 > {{{output/(tag+'.min.rpt')}}}
report_checks -path_delay max -to [all_registers -edge_triggered -data_pins] -group_count 1 -digits 6 > {{{output/(tag+'.capture.rpt')}}}
exit
'''
            script = output/(tag+'.tcl'); script.write_text(tcl)
            with (output/(tag+'.log')).open('w') as log:
                subprocess.run([str(sta),'-exit',str(script)],stdout=log,
                               stderr=subprocess.STDOUT,check=True,timeout=120)
            if 'Error:' in (output/(tag+'.log')).read_text():
                raise ValueError('Fixed-SPEF STA reported an error')
            row = {k:slack((output/(tag+'.'+ext+'.rpt')).read_text())
                   for k,ext in [('setup','max'),('hold','min'),('capture','capture')]}
            if case == 'baseline':
                for kind in ('setup','hold'):
                    expected = reference[f'timing__{kind}__ws__corner:nom_{corner}']
                    # Local OpenSTA2.6 and pinned CI differ by0.181ps on
                    # slow hold; keep setup at1fs, hold at1ps agreement.
                    tolerance = 1e-6 if kind == 'setup' else 1e-3
                    if not math.isfinite(expected) or abs(row[kind]-expected)>tolerance:
                        raise ValueError('Local baseline does not reproduce extracted CI')
                    row[kind+'_baseline_delta_ns'] = row[kind]-expected
            row.update(library_sha256=hashlib.sha256(lib.read_bytes()).hexdigest(),
                       macro_sha256=hashlib.sha256(macro.read_bytes()).hexdigest())
            results[case][corner] = row
            print(case,corner,json.dumps(row),flush=True)
    receipt = dict(source_run=review['evidence_run'],fixed_spef=True,physical_qualified=False,
                   official_signoff=False,connectivity_audited=True,
                   source_bindings=review['diagnostic_binding'],
                   sta_sha256=hashlib.sha256(Path(sta).read_bytes()).hexdigest(),cases=results)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('root','library_dir','macro_dir','sta','output'):
        parser.add_argument(arg,type=Path)
    a = parser.parse_args()
    diagnose(a.root,a.library_dir,a.macro_dir,a.sta,a.output)
