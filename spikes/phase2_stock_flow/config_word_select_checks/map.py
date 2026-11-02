"""Compare mapped cell area after check.py; this is not physical STA or die area."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('proved_work', type=Path)
    parser.add_argument('library', type=Path)
    args = parser.parse_args()
    base, work, library = (p.resolve() for p in (args.baseline, args.proved_work, args.library))
    package = Path(__file__).resolve().parent.parent
    evidence = json.loads((package / 'config_word_select_evidence.json').read_text())
    receipt = json.loads((work / 'receipt.json').read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if receipt['patch_sha256'] != evidence['patch_sha256']:
        raise ValueError('Wrong proof receipt')
    for folder, key in ((base, 'baseline_files'), (work, 'candidate_files')):
        for name, digest in receipt[key].items():
            if sha(folder / name) != digest:
                raise ValueError('Mapping source differs from proved source')
    env = os.environ.copy()
    env['PATH'] += ':' + str(Path.home() / 'oss-cad-suite/bin')
    results = {}
    for label, source in (('reference', base / 'src'), ('trial', work / 'src')):
        files = ' '.join(json.dumps(str(p)) for p in sorted(source.glob('*.v')))
        script = (f'read_liberty -lib -ignore_miss_func {json.dumps(str(library))}\n'
                  f'read_verilog -DSYNTHESIS -I{source} {files}\n'
                  'synth -top tt_um_tripwire -flatten -noabc\n'
                  f'dfflibmap -liberty {json.dumps(str(library))}\n'
                  f'abc -liberty {json.dumps(str(library))}\nclean\n'
                  f'tee -o {label}_stats.json stat -json -liberty {json.dumps(str(library))}\n'
                  f'write_verilog -noattr {label}_mapped.v\n')
        (work / (label + '_mapping.ys')).write_text(script)
        with (work / (label + '_mapping.log')).open('w') as log:
            subprocess.run(['yosys', '-Q', '-s', label + '_mapping.ys'], cwd=work, env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=300)
        stats = json.loads((work / (label + '_stats.json')).read_text())['design']
        results[label] = {k: stats[k] for k in ('area', 'sequential_area', 'num_cells', 'num_cells_by_type')}
    result = dict(cases=results, library_sha256=sha(library), physical_qualification=False,
                  scope='Comparative mapped cells; blackbox macro area and physical buffers/routes are excluded')
    (work / 'mapping_receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: {field: v[field] for field in ('area', 'num_cells', 'sequential_area')}
                      for k, v in results.items()}))


if __name__ == '__main__':
    main()
