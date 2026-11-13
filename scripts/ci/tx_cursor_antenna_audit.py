"""Read-only antenna comparison for the exact TX-cursor pending-drop failure."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

VIEWS = {'43-openroad-repairantennas': {'path': 'runs/stock-official-baseline/43-openroad-repairantennas/1-openroad-diodeinsertion/tt_um_tripwire.odb', 'sha256': 'dd2812c1bf5d67d6b478796a185677c96dd31f0e0ac1e3fb7e3c94ff33a1e947'}, '44-openroad-resizertimingpostgrt': {'path': 'runs/stock-official-baseline/44-openroad-resizertimingpostgrt/tt_um_tripwire.odb', 'sha256': '6c0fda50f9f87de2cc013871f02eeb98309cede91067d4409cf7e4956da3acf4'}}
IMAGE = 'ghcr.io/librelane/librelane@sha256:af2405f5d48d8fe14d406ecce913811177a95e365e3b625859677307cace2469'


def main():
    root = Path.cwd().resolve()
    run = json.loads(Path('tx-cursor-source-run.json').read_text())
    expected = dict(id=43338175616, head_sha='b477486f2d3ba5fbcb1a98bb5a87b5c93375d9b3', head_branch='main',
                    path='.github/workflows/gds-official-dev4-tx-cursor-screen.yaml', conclusion='failure')
    if any(run.get(k) != v for k,v in expected.items()):
        raise ValueError('Wrong TX-cursor source run')
    frozen=root/'frozen-screen'
    output=root/'runs/tx-cursor-antenna-audit'
    output.mkdir(parents=True, exist_ok=False)
    hashes={}
    for stage, view in VIEWS.items():
        odb=frozen/view['path']
        if hashlib.sha256(odb.read_bytes()).hexdigest()!=view['sha256']:
            raise ValueError('Wrong exact ODB checkpoint')
        hashes[stage]=view['sha256']
        report=output/(stage+'.rpt')
        tcl=output/(stage+'.tcl')
        tcl.write_text(f'read_db {{{odb}}}\n'
                       'set net [[ord::get_db_block] findNet _01949_]\n'
                       'if {$net == "NULL"} {error "Missing bound _01949_"}\n'
                       f'check_antennas -net _01949_ -verbose -report_file {{{report}}}\nexit\n')
        cmd=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
             '-v',f'{root}:{root}','-w',str(root),IMAGE,'openroad','-exit','-no_init',str(tcl)]
        with (output/(stage+'.log')).open('w') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        if not report.is_file() or '_01949_' not in report.read_text() or '_48904_/D' not in report.read_text():
            raise ValueError('Missing target-net geometry report')
        if hashlib.sha256(odb.read_bytes()).hexdigest()!=view['sha256']:
            raise ValueError('Read-only audit modified source database')
    (output/'receipt.json').write_text(json.dumps(dict(source_run=run['id'],source_sha=run['head_sha'],
        source_odb_hashes=hashes, net='_01949_', pin='_48904_/D', physical_repairs=False,
        qualified=False, official_signoff=False),indent=2)+'\n')


if __name__ == '__main__':
    main()
