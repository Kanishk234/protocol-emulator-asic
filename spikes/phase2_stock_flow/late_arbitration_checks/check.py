"""Replay whole-lane equivalence and reject a wrong urgent-winner mutant."""
import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path, help='Prepared full stock reference checkout')
    parser.add_argument('work', type=Path)
    parser.add_argument('--map-library', type=Path, help='Optional comparative mapping library; not signoff')
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[1]
    evidence = json.loads((package / 'late_arbitration_evidence.json').read_text())
    baseline, work = args.baseline.resolve(), args.work.resolve()
    patch = package / 'late_arbitration.patch'
    if sha(patch) != evidence['patch_sha256'] or sha(baseline / 'src/trw_lane.v') != evidence['baseline_sha256']:
        raise ValueError('Wrong patch or arbitration baseline')
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(baseline / 'src', work / 'src')
    before = {p.name: sha(p) for p in (work / 'src').iterdir() if p.is_file()}
    (work / 'gold_lane.v').write_bytes((work / 'src/trw_lane.v').read_bytes())
    subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(patch)], cwd=work, check=True)
    after = {p.name: sha(p) for p in (work / 'src').iterdir() if p.is_file()}
    if after != {**before, 'trw_lane.v': evidence['candidate_sha256']}:
        raise ValueError('Arbitration patch changed unexpected source bytes')
    script = '''read_verilog -DSYNTHESIS -Isrc src/trw_alu.v gold_lane.v
hierarchy -top trw_lane
proc
flatten
memory
opt
rename trw_lane gold
design -stash gold
read_verilog -DSYNTHESIS -Isrc src/trw_alu.v src/trw_lane.v
hierarchy -top trw_lane
proc
flatten
memory
opt
rename trw_lane gate
design -stash gate
design -copy-from gold -as gold gold
design -copy-from gate -as gate gate
equiv_make gold gate equiv
hierarchy -top equiv
equiv_simple
equiv_induct -seq 2
equiv_status -assert
'''
    env = os.environ.copy()
    env['PATH'] += ':' + str(Path.home() / 'oss-cad-suite/bin')

    def run(text, name):
        ys = work / (name + '.ys')
        ys.write_text(text)
        log = work / (name + '.log')
        with log.open('w') as stream:
            result = subprocess.run(['yosys', '-Q', '-s', str(ys)], cwd=work, env=env,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        return result.returncode, log.read_text()

    code, log = run(script, 'equivalence')
    match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', log)
    if code or not match or not int(match[1]) or 'Equivalence successfully proven!' not in log:
        raise ValueError('Whole-lane equivalence did not pass')
    trial = (work / 'src/trw_lane.v').read_text()
    wrong = trial.replace('urgent_ready & (~urgent_ready + 12\'d1)', 'first_ready')
    if wrong == trial:
        raise ValueError('Urgent-winner mutant was not applied')
    # A combinational arbitration contract gives a direct counterexample for
    # the mutant, without spending induction time on thousands of lane states.
    gold = (work / 'gold_lane.v').read_text()
    old_block = gold[gold.index('    // §4.3: with a step waiting'):gold.index('    wire [3:0] s_op')]
    new_block = trial[trial.index('    // Select the ready'):trial.index('    wire [3:0] s_op')]
    wrong_block = wrong[wrong.index('    // Select the ready'):wrong.index('    wire [3:0] s_op')]

    def contract(block):
        modules = []
        for name, body in (('original', old_block), ('changed', block)):
            modules.append(f'''module {name}(input [11:0] ready, urgent, input rt_ok,
 input [635:0] slots, output [52:0] selected, output fired, taken);
 localparam SB=53;
 {body}
 assign selected=ss; assign fired=fire; assign taken=rt_take;
 endmodule
''')
        return '\n'.join(modules) + '''
module contract(input [11:0] ready, urgent, input rt_ok, input [635:0] slots, output passed);
 wire [52:0] a,b; wire af,bf,at,bt;
 original u_a(ready,urgent,rt_ok,slots,a,af,at);
 changed u_b(ready,urgent,rt_ok,slots,b,bf,bt);
 assign passed = ({a,af,at} == {b,bf,bt});
endmodule
'''

    for label, block in (('correct-selection', new_block), ('wrong-urgent', wrong_block)):
        (work / (label + '.v')).write_text(contract(block))
        code, text = run(f'read_verilog -formal {label}.v\nprep -top contract -flatten\n'
                         'sat -prove passed 1 -verify\n', label)
        if label == 'correct-selection':
            if code or 'SUCCESS!' not in text:
                raise ValueError('Combinational winner contract did not pass')
        elif code == 0 or 'proof did fail' not in text:
            raise ValueError('Wrong urgent winner was not rejected by the contract')
    receipt = dict(proven_equivalence_points=int(match[1]), induction_sequence_cap=2,
                   negative_control='wrong urgent winner rejected',
                   candidate_sha256=after['trw_lane.v'], physical_qualification=False)
    if args.map_library:
        library = args.map_library.resolve()
        mapped = {}
        for label, source in (('gold', 'gold_lane.v'), ('trial', 'src/trw_lane.v')):
            script = f'''read_verilog -DSYNTHESIS -Isrc src/trw_alu.v {source}
synth -top trw_lane -flatten -noabc
dfflibmap -liberty "{library}"
abc -liberty "{library}"
clean
tee -o {label}_stats.json stat -json -liberty "{library}"
write_verilog -noattr {label}_mapped.v
'''
            code, _ = run(script, label + '-mapping')
            if code:
                raise ValueError('Comparative mapping failed')
            stats = json.loads((work / (label + '_stats.json')).read_text())['design']
            text = (work / (label + '_mapped.v')).read_text()
            drivers, endpoints = {}, {}
            for master, name, ports in re.findall(r'\b(sg13cmos5l_\w+)\s+(\\?\S+)\s*\((.*?)\);', text, re.S):
                pins = {pin: value.strip().lstrip('\\') for pin, value in re.findall(r'\.(\w+)\((.*?)\)', ports, re.S)}
                if 'dfrbpq' in master:
                    endpoints[pins['Q']] = pins['D']
                    continue
                output = 'X' if 'X' in pins else 'Y' if 'Y' in pins else None
                if output:
                    drivers[pins[output]] = [value for pin, value in pins.items() if pin != output]

            @functools.lru_cache(None)
            def depth(net):
                if net == 'mem_rdata[11]':
                    return 0
                values = [depth(pin) for pin in drivers.get(net, [])]
                values = [value for value in values if value is not None]
                return max(values) + 1 if values else None

            mapped[label] = dict(area_um2=stats['area'], cells=stats['num_cells'],
                                 sequential_area_um2=stats['sequential_area'],
                                 mem11_to_a_lat4_gate_levels=depth(endpoints['a_lat[4]']),
                                 max_mem11_to_flopD_gate_levels=max(value for value in (
                                     depth(pin) for pin in endpoints.values()) if value is not None))
        if mapped['gold']['sequential_area_um2'] != mapped['trial']['sequential_area_um2']:
            raise ValueError('Unexpected sequential mapping change')
        receipt['comparative_mapping'] = dict(library_sha256=sha(library), cases=mapped,
                                              routed_timing_proven=False,
                                              metric='unweighted combinational gate count, not STA')
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
