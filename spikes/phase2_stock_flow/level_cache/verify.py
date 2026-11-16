"""Reproduce scoped engine proofs on explicit reference/candidate source trees.

Run in the project venv. Logs/generated proof sources stay in a new output dir.
IDLE is modelled as root-clock storage, matching this ASIC candidate only.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    reference, candidate = args.reference.resolve(), args.candidate.resolve()
    evidence = json.loads(Path(__file__).with_name('candidate.json').read_text())
    for directory, key in ((reference, 'reference_files'), (candidate, 'candidate_files')):
        for name, digest in evidence[key].items():
            if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Proof source hash mismatch: ' + name)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for engine, parameter in (('tx', 'FULL'), ('bs', 'USE_SAMPLE_DELTA')):
        module = 'trw_pin_' + engine
        original = (reference / (module + '.v')).read_text()
        edited = (candidate / (module + '.v')).read_text()
        start = original.index('module ' + module + ' #(')
        header = original[start:original.index(');', start) + 2]
        ports = re.findall(r'^\s*(?:input|output)\s+(?:wire|reg)\s*(?:\[[^\]]+\]\s*)?(\w+)', header, re.M)
        assert 'idle' in ports
        for kind, text in (('gold', original), ('gate', edited)):
            (out / f'{kind}_module.v').write_text(text.replace('module ' + module + ' #(', 'module ' + kind + '_mod #(', 1))
            wrapper = header.replace('module ' + module + ' #(', 'module ' + kind + ' #(', 1).replace('output reg', 'output wire')
            connections = [f'.{port}({"idle_q" if port == "idle" else port})' for port in ports]
            if kind == 'gate':
                connections.append('.idle_next(idle)')
            params = ['.FULL(FULL)', '.FRAC(FRAC)'] if engine == 'tx' else ['.USE_SAMPLE_DELTA(USE_SAMPLE_DELTA)']
            if kind == 'gate':
                params.append('.USE_LEVEL_CACHE(1)')
            wrapper += '\nreg idle_q; always @(posedge clk) idle_q <= idle;\n'
            wrapper += f'{kind}_mod #({", ".join(params)}) uut({", ".join(connections)});\nendmodule\n'
            (out / f'{kind}_wrapper.v').write_text(wrapper)
        # opt_dff rewrites this private combinational mux output under enables.
        # It is not an architectural output or state; all ports remain checked.
        (out / 'comb_blacklist.txt').write_text('uut.nlvx\n')
        blacklist = '-blacklist comb_blacklist.txt ' if engine == 'tx' else ''
        for mutant in (False, True):
            gate = (out / 'gate_module.v').read_text()
            if mutant:
                assert 'lvl_q <= idle_next;' in gate
                gate = gate.replace('lvl_q <= idle_next;', 'lvl_q <= idle;')
            (out / 'selected_gate.v').write_text(gate)
            for value in (0, 1):
                script = (f'read_verilog -DSYNTHESIS -I{candidate} gold_module.v selected_gate.v gold_wrapper.v gate_wrapper.v; '
                          f'chparam -set {parameter} {value} gold; chparam -set {parameter} {value} gate; '
                          'hierarchy -check; proc; flatten gold gate; memory_map; opt; '
                          f'equiv_make {blacklist}gold gate equiv; hierarchy -top equiv; '
                          'equiv_simple; equiv_induct -seq 6; equiv_status -assert')
                stem = f'{engine}-{value}-' + ('stale-idle' if mutant else 'valid')
                (out / (stem + '.ys')).write_text(script + '\n')
                result = subprocess.run(['yosys', '-p', script], cwd=out, text=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
                (out / (stem + '.log')).write_text(result.stdout)
                if not mutant:
                    assert result.returncode == 0, stem
                else:
                    assert result.returncode != 0 and 'Unproven $equiv' in result.stdout, stem
                    assert ('\\lvl_gold' in result.stdout or '\\tx_lvl_gold' in result.stdout), stem
                points = re.findall(r'Found (\d+) \$equiv cells in equiv', result.stdout)
                results.append(dict(engine=engine, parameter=value, mutant=mutant,
                                    passed=not mutant, negative_control_rejected=mutant,
                                    points=int(points[-1]) if points else None))
                print(stem, 'OK', flush=True)
    (out / 'receipt.json').write_text(json.dumps(dict(results=results, physical_qualified=False,
        scope='Engine module proofs under root-clock IDLE contract; not whole-chip formal'), indent=2) + '\n')


if __name__ == '__main__':
    main()
