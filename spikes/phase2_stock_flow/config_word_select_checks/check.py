"""Replay source-bound host decode equivalence and configuration phase checks.

BASE is the prepared clock100 full-design checkout; WORK must not exist.
This proves named interfaces/properties, not physical timing or whole-chip formal.
"""
import argparse
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
    parser.add_argument('baseline', type=Path)
    parser.add_argument('work', type=Path)
    args = parser.parse_args()
    checks = Path(__file__).resolve().parent
    package = checks.parent
    evidence = json.loads((package / 'config_word_select_evidence.json').read_text())
    base, work = args.baseline.resolve(), args.work.resolve()
    patch = package / 'config_word_select.patch'
    if sha(patch) != evidence['patch_sha256']:
        raise ValueError('Changed write-select patch')
    for name, expected in evidence['baseline_files'].items():
        if sha(base / name) != expected:
            raise ValueError('Wrong source baseline: ' + name)
    if sha(base / 'src/trw_defs.vh') != evidence['defines_sha256']:
        raise ValueError('Wrong source encodings')
    definitions = (base / 'src/trw_defs.vh').read_text()
    if "`define TRW_HA_PIN_CFG 16'h3000" not in definitions:
        raise ValueError('Configuration base alignment is not the proved encoding')
    work.mkdir(parents=True, exist_ok=False)
    shutil.copytree(base / 'src', work / 'src')
    fingerprints = lambda: {str(p.relative_to(work)): sha(p)
                            for p in (work / 'src').rglob('*') if p.is_file()}
    before = fingerprints()
    subprocess.run(['patch', '--batch', '--forward', '-p1', '-i', str(patch)], cwd=work, check=True)
    if fingerprints() != {**before, **evidence['candidate_files']}:
        raise ValueError('Unexpected write-select source delta')

    gold = (base / 'src/trw_spi.v').read_text().replace('module trw_spi (', 'module gold_spi (')
    gold = gold.replace('    output reg  [15:0] wr_addr,',
                        '    output reg  [15:0] wr_addr,\n    output wire [7:0] wr_addr_hi_sel,')
    gold = gold.replace('endmodule', "assign wr_addr_hi_sel = 8'd1 << wr_addr[4:2];\nendmodule")
    (work / 'gold_spi.v').write_text(gold)
    gold = (base / 'src/trw_host.v').read_text().replace('module trw_host #(', 'module gold_host #(')
    gold = gold.replace('    trw_spi u_spi (', '    gold_spi u_spi (')
    gold = gold.replace('    output wire [4:0]        pcfg_waddr,',
                        '    output wire [4:0]        pcfg_waddr,\n'
                        '    output wire [`TRW_PC_WORDS-1:0] pcfg_word_sel,')
    gold = gold.replace('endmodule', "assign pcfg_word_sel = 32'd1 << pcfg_waddr;\nendmodule")
    (work / 'gold_host.v').write_text(gold)
    (work / 'gold_pin_cfg.v').write_text((base / 'src/trw_pin_cfg.v').read_text().replace(
        'module trw_pin_cfg #(', 'module gold_pin_cfg #('))
    for name in ('contract.v', 'tb_cache.v'):
        shutil.copy2(checks / name, work / name)
    env = os.environ.copy()
    env['PATH'] += ':' + str(Path.home() / 'oss-cad-suite/bin')

    def proof(script, name, *, negative=False):
        (work / (name + '.ys')).write_text(script)
        log = work / (name + '.log')
        with log.open('w') as stream:
            result = subprocess.run(['yosys', '-Q', '-s', name + '.ys'], cwd=work,
                                    env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        text = log.read_text()
        if negative:
            if result.returncode == 0 or not ('proof did fail' in text or
                                             re.search(r'ERROR: Found \d+ unproven', text)):
                raise ValueError('Negative control did not fail its property: ' + name)
        elif result.returncode != 0:
            raise ValueError('Proof failed: ' + name)
        return text

    points = {}
    scripts = [('spi', (checks / 'spi_equiv.ys').read_text())]
    for nl, nu, nc in ((2, 4, 9), (3, 6, 13)):
        script = (checks / 'host_equiv.ys').read_text()
        for key, value in (('NL', nl), ('NU', nu), ('NC', nc)):
            script = script.replace('@' + key + '@', str(value))
        scripts.append((f'host_{nl}_{nu}', script))
    for name, script in scripts:
        text = proof(script, name)
        match = re.search(r'Of those cells (\d+) are proven and 0 are unproven', text)
        if not match or 'Equivalence successfully proven!' not in text:
            raise ValueError('Missing equivalence result: ' + name)
        points[name] = int(match[1])
    source = (work / 'src/trw_spi.v').read_text()
    wrong = source.replace("8'd1 << addr[4:2]", "8'd1 << (addr[4:2] ^ 3'd1)")
    if wrong == source:
        raise ValueError('SPI mutant was not applied')
    (work / 'wrong_spi.v').write_text(wrong)
    proof(scripts[0][1].replace('src/trw_spi.v', 'wrong_spi.v'), 'wrong_spi', negative=True)

    phase_cases = []
    for mode in ('latch', 'flop'):
        define = ['-DTRW_PIN_CFG_FLOPS'] if mode == 'flop' else []
        for full in (0, 1):
            name = f'cfg_{mode}_{full}'
            script = ('read_verilog -formal ' + ' '.join(define)
                      + ' -Isrc src/trw_pin_cfg.v gold_pin_cfg.v contract.v\n'
                      + f'chparam -set FULL {full} select_contract\n'
                      + 'prep -top select_contract -flatten\nclk2fflogic\nopt -full\n'
                      + 'sat -tempinduct -seq 4 -maxsteps 16 -prove-asserts -set-assumes -verify\n')
            if 'SUCCESS!' not in proof(script, name):
                raise ValueError('Missing configuration proof result')
            subprocess.run(['iverilog', '-g2005', *define, '-Isrc', '-s', 'tb_cache',
                            f'-Ptb_cache.FULL={full}', '-o', name, 'tb_cache.v',
                            'gold_pin_cfg.v', 'src/trw_pin_cfg.v'], cwd=work, env=env, check=True)
            result = subprocess.run(['vvp', name], cwd=work, env=env, text=True,
                                    capture_output=True, timeout=60, check=True)
            (work / (name + '-simulation.log')).write_text(result.stdout)
            if 'PASS bank:' not in result.stdout:
                raise ValueError('Missing configuration simulation pass')
            phase_cases.append(name)
            if name == 'cfg_latch_1':
                body = (work / 'contract.v').read_text()
                wrong = body.replace("32'd1 << waddr", "32'd1 << (waddr ^ 5'd1)")
                if wrong == body:
                    raise ValueError('Configuration mutant was not applied')
                (work / 'wrong_contract.v').write_text(wrong)
                proof(script.replace('contract.v', 'wrong_contract.v'), 'wrong_cfg', negative=True)
    if fingerprints() != {**before, **evidence['candidate_files']}:
        raise ValueError('Source changed during verification')
    receipt = dict(equivalence_points=points, equivalence_induction_sequence_cap=2,
                   phase_cases=phase_cases, negative_controls=['wrong SPI group', 'wrong config word'],
                   patch_sha256=sha(patch), baseline_files=before, candidate_files=fingerprints(),
                   physical_qualification=False)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
